from base64 import b64decode
from io import BytesIO
import os
import sys
import warnings
warnings.simplefilter('ignore', UserWarning)
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from torch import optim

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import random
from multiprocessing import Queue
from multiprocessing.synchronize import Event as Event_
from pathlib import Path

import imageio
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from constant import *
from imageio import get_writer
from PIL import Image
from torch import nn
from torch.optim import Adam
from torchvision.transforms.transforms import Compose

from .biggan import BigGAN
from .clip import CLIP, load, tokenize
from .ema import EMA
from .resample import resample

logger: Logger = get_logger()

# helpers

def exists(val: Any) -> bool:
    return val is not None


def create_text_path(text: Optional[str] = None) -> str:
    input_name: str = ""

    if text is not None:
        input_name += text

    return input_name.replace("-", "_").replace(",", "").replace(" ", "_").replace("|", "--").strip('-_')[:255]

# tensor helpers

def differentiable_topk(x, k, temperature=1.):
    n, dim = x.shape
    topk_tensors = []

    for i in range(k):
        is_last = i == (k - 1)
        values, indices = (x / temperature).softmax(dim=-1).topk(1, dim=-1)
        topks = torch.zeros_like(x).scatter_(-1, indices, values)
        topk_tensors.append(topks)
        if not is_last:
            x = x.scatter(-1, indices, float('-inf'))

    topks = torch.cat(topk_tensors, dim=-1)

    return topks.reshape(n, k, dim).sum(dim = 1)


def create_clip_img_transform(image_width: int) -> Compose:
    clip_mean: List[float] = [0.48145466, 0.4578275, 0.40821073]
    clip_std: List[float] = [0.26862954, 0.26130258, 0.27577711]
    transform: Compose = T.Compose([
        T.Resize(image_width),
        T.CenterCrop((image_width, image_width)),
        T.ToTensor(),
        T.Normalize(mean=clip_mean, std=clip_std)
    ])

    return transform


def rand_cutout(image: torch.Tensor, size: int, center_bias: bool = False, center_focus: int = 2) -> torch.Tensor:
    width = image.shape[-1]
    min_offset = 0
    max_offset = width - size
    if center_bias:
        # sample around image center
        center = max_offset / 2
        std = center / center_focus
        offset_x = int(random.gauss(mu=center, sigma=std))
        offset_y = int(random.gauss(mu=center, sigma=std))

        # resample uniformly if over boundaries
        offset_x = random.randint(min_offset, max_offset) if (offset_x > max_offset or offset_x < min_offset) else offset_x
        offset_y = random.randint(min_offset, max_offset) if (offset_y > max_offset or offset_y < min_offset) else offset_y
    else:
        offset_x = random.randint(min_offset, max_offset)
        offset_y = random.randint(min_offset, max_offset)
    cutout = image[:, :, offset_x:offset_x + size, offset_y:offset_y + size]

    return cutout


# load biggan

class Latents(nn.Module):
    def __init__(
        self,
        num_latents = 15,
        num_classes = 1000,
        z_dim = 128,
        max_classes = None,
        class_temperature = 2.
    ):
        super().__init__()
        self.normu = nn.Parameter(torch.zeros(num_latents, z_dim).normal_(std = 1))
        self.cls = nn.Parameter(torch.zeros(num_latents, num_classes).normal_(mean = -3.9, std = .3))
        self.register_buffer('thresh_lat', torch.tensor(1))

        assert not exists(max_classes) or max_classes > 0 and max_classes <= num_classes, f'max_classes must be between 0 and {num_classes}'

        self.max_classes = max_classes
        self.class_temperature = class_temperature

    def forward(self):
        if exists(self.max_classes):
            classes = differentiable_topk(self.cls, self.max_classes, temperature = self.class_temperature)
        else:
            classes = torch.sigmoid(self.cls)

        return self.normu, classes

class Model(nn.Module):
    def __init__(
        self,
        image_width,
        max_classes = None,
        class_temperature = 2.,
        ema_decay = 0.99
    ):
        super().__init__()
        
        assert image_width in (128, 256, 512), 'image size must be one of 128, 256, or 512'

        self.biggan = BigGAN.from_pretrained(f'biggan-deep-{image_width}', cache_dir=PRETRAINED_BACKBONE_MODEL_PATH)
        self.max_classes = max_classes
        self.class_temperature = class_temperature
        self.ema_decay\
            = ema_decay

        self.init_latents()

    def init_latents(self):
        latents = Latents(
            num_latents = len(self.biggan.config.layers) + 1,
            num_classes = self.biggan.config.num_classes,
            z_dim = self.biggan.config.z_dim,
            max_classes = self.max_classes,
            class_temperature = self.class_temperature
        )
        self.latents = EMA(latents, self.ema_decay)

    def forward(self):
        self.biggan.eval()
        out = self.biggan(*self.latents(), 1)
        return (out + 1) / 2


class BigSleep(nn.Module):
    def __init__(
        self,
        clip_model: Tuple[CLIP, Compose],
        num_cutouts = 128,
        loss_coef = 100,
        image_width = 512,
        bilinear = False,
        max_classes = None,
        class_temperature = 2.,
        experimental_resample = False,
        ema_decay = 0.99,
        center_bias = False,
    ):
        super().__init__()
        self.loss_coef = loss_coef
        self.image_width = image_width
        self.num_cutouts = num_cutouts
        self.experimental_resample = experimental_resample
        self.center_bias = center_bias

        self.interpolation_settings = {'mode': 'bilinear', 'align_corners': False} if bilinear else {'mode': 'nearest'}

        self.perceptor: CLIP = clip_model[0]
        self.normalize_image: Compose = clip_model[1]

        self.model = Model(
            image_width = image_width,
            max_classes = max_classes,
            class_temperature = class_temperature,
            ema_decay = ema_decay
        )

    def reset(self):
        self.model.init_latents()

    def sim_txt_to_img(self, text_embed, img_embed, text_type="max"):
        sign = -1
        if text_type == "min":
            sign = 1
        return sign * self.loss_coef * torch.cosine_similarity(text_embed, img_embed, dim = -1).mean()

    def forward(self, text_embeds, stick_embeds=[], return_loss = True):
        width, num_cutouts = self.image_width, self.num_cutouts

        out = self.model()

        if not return_loss:
            return out

        pieces = []
        for ch in range(num_cutouts):
            # sample cutout size
            size = int(width * torch.zeros(1,).normal_(mean=.8, std=.3).clip(.5, .95))
            # get cutout
            apper = rand_cutout(out, size, center_bias=self.center_bias)
            if (self.experimental_resample):
                apper = resample(apper, (224, 224))
            else:
                apper = F.interpolate(apper, (224, 224), **self.interpolation_settings)
            pieces.append(apper)

        into = torch.cat(pieces)
        into = self.normalize_image(into)

        image_embed = self.perceptor.encode_image(into)

        latents, soft_one_hot_classes = self.model.latents()
        num_latents = latents.shape[0]
        latent_thres = self.model.latents.model.thresh_lat

        lat_loss =  torch.abs(1 - torch.std(latents, dim=1)).mean() + \
                    torch.abs(torch.mean(latents, dim = 1)).mean() + \
                    4 * torch.max(torch.square(latents).mean(), latent_thres)


        for array in latents:
            mean = torch.mean(array)
            diffs = array - mean
            var = torch.mean(torch.pow(diffs, 2.0))
            std = torch.pow(var, 0.5)
            zscores = diffs / std
            skews = torch.mean(torch.pow(zscores, 3.0))
            kurtoses = torch.mean(torch.pow(zscores, 4.0)) - 3.0

            lat_loss = lat_loss + torch.abs(kurtoses) / num_latents + torch.abs(skews) / num_latents

        cls_loss = ((50 * torch.topk(soft_one_hot_classes, largest = False, dim = 1, k = 999)[0]) ** 2).mean()

        results = []
        for txt_embed in text_embeds:
            results.append(self.sim_txt_to_img(txt_embed, image_embed))
        for txt_min_embed in stick_embeds:
            results.append(self.sim_txt_to_img(txt_min_embed, image_embed, "min"))
        sim_loss = sum(results).mean()

        return out, (lat_loss, cls_loss, sim_loss)


class Imagine(nn.Module):
    def __init__(
        self,
        client_uuid: str,
        client_data: Dict[str, Union[str, Queue]],
        img: Optional[str] = None,
        lr: float = 0.07,
        epochs: int = 1,
        bilinear = False,
        max_classes = None,
        class_temperature = 2.,
        experimental_resample = False,
        ema_decay = 0.99,
        num_cutouts = 128,
        center_bias = True,
    ):
        super().__init__()

        self.client_uuid: str = client_uuid
        self.client_data: Dict[str, Union[str, Queue]] = client_data

        self.save_img_path: str = self.client_data[JSON_IMG_PATH]
        self.response_img_path: str = self.client_data[JSON_IMG_PATH].replace("frontend/", "")
        save_mp4_path: str = os.path.join(self.client_data[JSON_MP4_PATH], "timelapse.mp4")
        self.response_mp4_path: str = save_mp4_path.replace("frontend/", "")

        self.writer: imageio.core.Format.Writer = get_writer(save_mp4_path, fps=20)

        text: str = f"{self.client_data[RECEIVED_DATA][JSON_TEXT]}|{self.client_data[RECEIVED_DATA][JSON_CARROT]}"
        stick: str = self.client_data[RECEIVED_DATA][JSON_STICK]
        seed: Optional[int] = self.client_data[RECEIVED_DATA][JSON_SEED]
        image_width: int = int(self.client_data[RECEIVED_DATA][JSON_SIZE])
        iterations: int = int(self.client_data[RECEIVED_DATA][JSON_TOTAL_ITER])
        gradient_accumulate_every: int = int(self.client_data[RECEIVED_DATA][JSON_GAE])
        model_name: str = self.client_data[RECEIVED_DATA][JSON_BACKBONE]
        if self.client_data[RECEIVED_DATA][JSON_SOURCE_IMG] is not None:
            source_img: Image = Image.open(BytesIO(b64decode((self.client_data[RECEIVED_DATA][JSON_SOURCE_IMG])))).convert('RGB')
        else:
            source_img = None

        self.c2i_queue: Queue = self.client_data[CORE_C2I_QUEUE]
        self.c2i_brake_queue: Queue = self.client_data[CORE_C2I_BREAK_QUEUE]
        self.c2i_event: Event_ = self.client_data[CORE_C2I_EVENT]
        self.i2c_event: Event_ = self.client_data[CORE_I2C_EVENT]

        self.put_data: Dict[str, Optional[Union[str, bool]]] = {
            JSON_HASH: self.client_uuid,
            JSON_CURRENT_ITER: None,
            JSON_IMG_PATH: None,
            JSON_MP4_PATH: self.response_mp4_path,
            JSON_COMPLETE: False,
            JSON_MODEL_STATUS: False,
        }


        if exists(seed):
            self.seed: int = seed
            logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Seed is manually set to {self.seed}")
            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
            random.seed(seed)
            torch.backends.cudnn.deterministic = True
        else:
            self.seed = random.randint(-sys.maxsize - 1, sys.maxsize)
            logger.info(f"[{self.client_uuid}]: <<AIcon Core>> No seed is specified. It will automatically be set to {self.seed}")
            torch.backends.cudnn.benchmark = True

        self.epochs: int = epochs
        self.iterations: int = iterations

        jit: bool = True

        # jit models only compatible with version CORE_COMPATIBLE_PYTORCH_VERSION
        if CORE_COMPATIBLE_PYTORCH_VERSION not in torch.__version__:
            if jit:
                logger.warning(f"[{self.client_uuid}]: <<AIcon Core>> Setting jit to False because torch version is not {CORE_COMPATIBLE_PYTORCH_VERSION}")
            jit = False

        clip_model: Tuple[CLIP, Compose] = load(model_name, jit=jit)
        self.perceptor, _ = clip_model

        model: BigSleep = BigSleep(
            image_width=image_width,
            bilinear=bilinear,
            max_classes=max_classes,
            class_temperature=class_temperature,
            experimental_resample=experimental_resample,
            ema_decay=ema_decay,
            num_cutouts=num_cutouts,
            center_bias=center_bias,
            clip_model=clip_model,
        ).cuda()

        self.model: BigSleep = model

        self.lr: float = lr
        self.optimizer: optim.Adam = Adam(model.model.latents.model.parameters(), lr)
        self.gradient_accumulate_every: int = gradient_accumulate_every

        self.total_image_updates: int = self.epochs * self.iterations
        self.encoded_texts: Dict[str, list] = {
            "max": [],
            "min": []
        }

        # create img transform
        self.clip_transform = create_clip_img_transform(224)

        # create starting encoding
        self.set_clip_encoding(text=text, img=source_img, stick=stick)

    def set_text(self, text: Optional[str] = None) -> None:
        self.set_clip_encoding(text=text)

    def create_clip_encoding(self, text: Optional[str] = None, img: Optional[str] = None) -> torch.Tensor:
        self.text = text
        self.img = img

        if text is not None and img is not None:
            encoding: torch.Tensor = (self.create_text_encoding(text) + self.create_img_encoding(img)) / 2
        elif text is not None:
            encoding = self.create_text_encoding(text)
        elif img is not None:
            encoding = self.create_img_encoding(img)

        return encoding

    def create_text_encoding(self, text: str) -> torch.Tensor:
        tokenized_text: torch.Tensor = tokenize(text).cuda()
        with torch.no_grad():
            text_encoding: torch.Tensor = self.perceptor.encode_text(tokenized_text).detach()

        return text_encoding
    
    def create_img_encoding(self, img: str) -> torch.Tensor:
        normed_img: torch.Tensor = self.clip_transform(img).unsqueeze(0).cuda()

        with torch.no_grad():
            img_encoding: torch.Tensor = self.perceptor.encode_image(normed_img).detach()

        return img_encoding
    
    
    def encode_multiple_phrases(self, text: Optional[str] = None, img: Optional[str] = None, text_type: str = "max") -> None:
        if text is not None and "|" in text:
            self.encoded_texts[text_type] = [self.create_clip_encoding(text=prompt_min, img=img) for prompt_min in text.split("|")]
        else:
            self.encoded_texts[text_type] = [self.create_clip_encoding(text=text, img=img)]

    def encode_max_and_min(self, text: Optional[str] = None, img: Optional[str] = None, stick: str = "") -> None:
        self.encode_multiple_phrases(text, img=img)
        if stick is not None and stick != "":
            self.encode_multiple_phrases(stick, img=img, text_type="min")

    def set_clip_encoding(self, text: Optional[str] = None, img: Optional[str] = None, stick: str = "") -> None:
        self.text = text
        self.stick = stick
        
        if len(stick) > 0:
            text = text + "_wout_" + stick[:255] if text is not None else "wout_" + stick[:255]
        text_path = create_text_path(text=text)

        self.text_path = text_path
        self.filename = Path(f'./{text_path}.png')
        self.encode_max_and_min(text, img=img, stick=stick) # Tokenize and encode each prompt

    def reset(self) -> None:
        self.model.reset()
        self.model = self.model.cuda()
        self.optimizer = Adam(self.model.model.latents.parameters(), self.lr)
    
    def get_output_img_path(self, sequence_number: Optional[int]) -> Tuple[Path, Path]:
        """
        Returns underscore separated Path.
        :rtype: Path
        """
        output_path: str = self.text_path
        save_output_path: str = os.path.join(self.save_img_path, f"{output_path}.{sequence_number:06d}")
        response_output_path: str = os.path.join(self.response_img_path, f"{output_path}.{sequence_number:06d}")

        return (Path(f"{save_output_path}.png"), Path(f"{response_output_path}.png"))

    def get_img_sequence_number(self, epoch: int, iteration: int) -> int:
        sequence_number: int = epoch * self.iterations + iteration

        return sequence_number

    def train_step(self, epoch: int, iteration: int) -> None:
        total_loss = 0

        for _ in range(self.gradient_accumulate_every):
            _, losses = self.model(self.encoded_texts["max"], self.encoded_texts["min"])
            loss = sum(losses) / self.gradient_accumulate_every
            total_loss += loss
            loss.backward()

        self.optimizer.step()
        self.model.model.latents.update()
        self.optimizer.zero_grad(set_to_none=True)

        self.save_image(epoch, iteration)

    @torch.no_grad()
    def save_image(self, epoch: int, iteration: int) -> None:
        self.model.model.latents.eval()

        _, losses = self.model(self.encoded_texts["max"], self.encoded_texts["min"])
        top_score, best = torch.topk(losses[2], k=1, largest=False)

        img: torch.Tensor = self.model.model()[best].cpu().float().clamp(0., 1.)

        self.model.model.latents.train()

        sequence_number: int = self.get_img_sequence_number(epoch, iteration)

        save_filename, self.response_filename = self.get_output_img_path(sequence_number=sequence_number)
        
        pil_img: Image = T.ToPILImage()(img.squeeze())
        pil_img.save(save_filename)

        self.writer.append_data(np.uint8(np.array(pil_img)))

    def forward(self) -> None:      
        with torch.no_grad():
            self.model(self.encoded_texts["max"][0]) # one warmup step due to issue with CLIP and CUDA

        self.put_data[JSON_MODEL_STATUS] = True
        self.c2i_queue.put_nowait(self.put_data)

        try:
            for epoch in range(self.epochs):
                for iteration in range(self.iterations):
                    if self.i2c_event.is_set():
                        raise AIconAbortedError("Abort signal detected")

                    sequence_number: int = self.get_img_sequence_number(epoch, iteration)
    
                    self.train_step(epoch, iteration)

                    self.put_data[JSON_CURRENT_ITER] = int(sequence_number)
                    self.put_data[JSON_IMG_PATH] = str(self.response_filename)

                    self.c2i_queue.put_nowait(self.put_data)

                    logger.debug(f"[{self.client_uuid}]: <<AIcon Core>> Processing... {sequence_number + 1}/{self.iterations * self.epochs}")

        except KeyboardInterrupt as e:
            raise e

        except RuntimeError as e:
            if 'out of memory' in str(e):
                raise AIconOutOfMemoryError(str(e))
            else:
                raise AIconRuntimeError(str(e))

        except AIconAbortedError as e:
            raise e

        finally:
            self.save_image(epoch, iteration)
            self.writer.close()

            try:
                self.put_data[JSON_CURRENT_ITER] = int(sequence_number)
            except UnboundLocalError:
                pass

            self.put_data[JSON_IMG_PATH] = str(self.response_filename)

            self.c2i_queue.put_nowait(self.put_data)
            self.c2i_brake_queue.put_nowait(self.put_data)
            self.c2i_event.set()

            torch.cuda.empty_cache()
