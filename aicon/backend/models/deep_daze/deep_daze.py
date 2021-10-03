from io import BytesIO
import os
import sys
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import imageio
from torch import optim

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import random
from multiprocessing import Queue
from multiprocessing.synchronize import Event as Event_
from pathlib import Path
from base64 import b64decode

import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from constant import *
from imageio import get_writer
from PIL import Image
from siren_pytorch import SirenNet, SirenWrapper
from torch import nn
from torch.cuda.amp import GradScaler, autocast
from torch.nn.parameter import Parameter
from torch_optimizer import AdamP, DiffGrad
from torchvision.transforms.transforms import Compose

from .clip import load, tokenize

logger: Logger = get_logger()

# Helpers

def exists(val: Any) -> bool:
    return val is not None


def default(val: Any, d: Any) -> Any:
    return val if exists(val) else d


def interpolate(image: torch.Tensor, size: int) -> torch.Tensor:
    return F.interpolate(image, (size, size), mode='bilinear', align_corners=False)


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


def norm_siren_output(img):
    return ((img + 1) * 0.5).clamp(0.0, 1.0)


def create_text_path(context_length: int, text: Optional[str] = None, target_img: Optional[str] = None, separator: Optional[str] = None) -> str:
    if text is not None:
        if separator is not None and separator in text:
            text = text[:text.index(separator, )]
        input_name = text.replace(" ", "_")[:context_length]
    elif target_img is not None:
        input_name = "".join(target_img.replace(" ", "_").split(".")[:-1])
    else:
        input_name = "your_encoding"

    return input_name


class DeepDaze(nn.Module):
    def __init__(
            self,
            clip_perceptor,
            clip_norm,
            input_res,
            total_batches,
            batch_size,
            num_layers=8,
            image_width=512,
            loss_coef=100,
            theta_initial=None,
            theta_hidden=None,
            lower_bound_cutout=0.1, # should be smaller than 0.8
            upper_bound_cutout=1.0,
            saturate_bound=False,
            gauss_sampling=False,
            gauss_mean=0.6,
            gauss_std=0.2,
            do_cutout=True,
            center_bias=False,
            center_focus=2,
            hidden_size=256,
            averaging_weight=0.3,
    ):
        super().__init__()
        # load clip
        self.perceptor = clip_perceptor
        self.input_resolution = input_res
        self.normalize_image = clip_norm
        
        self.loss_coef = loss_coef
        self.image_width = image_width

        self.batch_size = batch_size
        self.total_batches = total_batches
        self.num_batches_processed = 0

        w0 = default(theta_hidden, 30.)
        w0_initial = default(theta_initial, 30.)

        siren = SirenNet(
            dim_in=2,
            dim_hidden=hidden_size,
            num_layers=num_layers,
            dim_out=3,
            use_bias=True,
            w0=w0,
            w0_initial=w0_initial
        )

        self.model = SirenWrapper(
            siren,
            image_width=image_width,
            image_height=image_width
        )

        self.saturate_bound = saturate_bound
        self.saturate_limit = 0.75  # cutouts above this value lead to destabilization
        self.lower_bound_cutout = lower_bound_cutout
        self.upper_bound_cutout = upper_bound_cutout
        self.gauss_sampling = gauss_sampling
        self.gauss_mean = gauss_mean
        self.gauss_std = gauss_std
        self.do_cutout = do_cutout
        self.center_bias = center_bias
        self.center_focus = center_focus
        self.averaging_weight = averaging_weight
        
    def sample_sizes(self, lower, upper, width, gauss_mean):
        if self.gauss_sampling:
            gauss_samples = torch.zeros(self.batch_size).normal_(mean=gauss_mean, std=self.gauss_std)
            outside_bounds_mask = (gauss_samples > upper) | (gauss_samples < upper)
            gauss_samples[outside_bounds_mask] = torch.zeros((len(gauss_samples[outside_bounds_mask]),)).uniform_(lower, upper)
            sizes = (gauss_samples * width).int()
        else:
            lower *= width
            upper *= width
            sizes = torch.randint(int(lower), int(upper), (self.batch_size,))
        return sizes

    def forward(self, text_embed, return_loss=True, dry_run=False) -> Union[torch.Tensor, Tuple[torch.Tensor, ...]]:
        out = self.model()
        out = norm_siren_output(out)

        if not return_loss:
            return out
                
        # determine upper and lower sampling bound
        width = out.shape[-1]
        lower_bound = self.lower_bound_cutout
        if self.saturate_bound:
            progress_fraction = self.num_batches_processed / self.total_batches
            lower_bound += (self.saturate_limit - self.lower_bound_cutout) * progress_fraction

        # sample cutout sizes between lower and upper bound
        sizes = self.sample_sizes(lower_bound, self.upper_bound_cutout, width, self.gauss_mean)

        # create normalized random cutouts
        if self.do_cutout:   
            image_pieces = [rand_cutout(out, size, center_bias=self.center_bias, center_focus=self.center_focus) for size in sizes]
            image_pieces = [interpolate(piece, self.input_resolution) for piece in image_pieces]
        else:
            image_pieces = [interpolate(out.clone(), self.input_resolution) for _ in sizes]

        # normalize
        image_pieces = torch.cat([self.normalize_image(piece) for piece in image_pieces])
        
        # calc image embedding
        with autocast(enabled=False):
            image_embed = self.perceptor.encode_image(image_pieces)
            
        # calc loss
        # loss over averaged features of cutouts
        avg_image_embed = image_embed.mean(dim=0).unsqueeze(0)
        averaged_loss = -self.loss_coef * torch.cosine_similarity(text_embed, avg_image_embed, dim=-1).mean()
        # loss over all cutouts
        general_loss = -self.loss_coef * torch.cosine_similarity(text_embed, image_embed, dim=-1).mean()
        # merge losses
        loss = averaged_loss * (self.averaging_weight) + general_loss * (1 - self.averaging_weight)

        # count batches
        if not dry_run:
            self.num_batches_processed += self.batch_size
        
        return out, loss


class Imagine(nn.Module):
    def __init__(
            self,
            client_uuid: str,
            client_data: Dict[str, Union[str, Queue]],
            lr: float = 0.0001,
            optimizer: str = "AdamP",
            center_bias: bool = True,
            center_focus: int = 2,
            jit: bool = True,
            epochs: int = 1,
            start_image_train_iters: int = 50,
            start_image_lr: float = 3e-4,
            theta_initial: Optional[float] = None,
            theta_hidden: Optional[float] = None,
            lower_bound_cutout: float = 0.1,
            upper_bound_cutout: float = 1.0,
            saturate_bound: bool = False,
            averaging_weight: bool = 0.3,
            create_story: bool = False,
            story_start_words: int = 5,
            story_words_per_epoch: int = 5,
            story_separator: Optional[str] = None,
            gauss_sampling: bool = False,
            gauss_mean: float = 0.6,
            gauss_std: float = 0.2,
            do_cutout: bool = True,
            clip_encoding=None,
    ): 
        super().__init__()

        self.client_uuid: str = client_uuid
        self.client_data: Dict[str, Union[str, Queue]] = client_data

        self.save_img_path: str = self.client_data[JSON_IMG_PATH]
        self.response_img_path: str = self.client_data[JSON_IMG_PATH].replace("frontend/", "")
        save_mp4_path: str = os.path.join(self.client_data[JSON_MP4_PATH], "timelapse.mp4")
        self.response_mp4_path: str = save_mp4_path.replace("frontend/", "")

        self.writer: imageio.core.Format.Writer = get_writer(save_mp4_path, fps=20)

        text: str = self.client_data[RECEIVED_DATA][JSON_TEXT]
        seed: Optional[int] = self.client_data[RECEIVED_DATA][JSON_SEED]
        image_width: int = int(self.client_data[RECEIVED_DATA][JSON_SIZE])
        iterations: int = int(self.client_data[RECEIVED_DATA][JSON_TOTAL_ITER])
        batch_size: int = int(self.client_data[RECEIVED_DATA][JSON_BATCH_SIZE])
        gradient_accumulate_every: int = int(self.client_data[RECEIVED_DATA][JSON_GAE])
        num_layers: int = int(self.client_data[RECEIVED_DATA][JSON_NUM_LAYER])
        hidden_size: int = int(self.client_data[RECEIVED_DATA][JSON_HIDDEN_SIZE])
        model_name: str = str(self.client_data[RECEIVED_DATA][JSON_BACKBONE])
        if self.client_data[RECEIVED_DATA][JSON_SOURCE_IMG] is not None:
            source_img: bytes = BytesIO(b64decode((self.client_data[RECEIVED_DATA][JSON_SOURCE_IMG])))
        else:
            source_img = None
        if self.client_data[RECEIVED_DATA][JSON_TARGET_IMG] is not None:
            target_img: bytes = BytesIO(b64decode((self.client_data[RECEIVED_DATA][JSON_TARGET_IMG])))
        else:
            target_img = None

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
            
        # fields for story creation:
        self.create_story: bool = create_story
        self.words: Optional[str] = None
        self.separator: Optional[str] = str(story_separator) if story_separator is not None else None

        if self.separator is not None and text is not None:
            #exit if text is just the separator
            if str(text).replace(' ','').replace(self.separator,'') == '':
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> Text only consists of the separator `{self.separator}`")
                raise AIconValueError(f"Text only consists of the separator `{self.separator}`")

            #adds a space to each separator and removes double spaces that might be generated
            text = text.replace(self.separator,self.separator+' ').replace('  ',' ').strip()

        self.all_words: Optional[str] = text.split(" ") if text is not None else None
        self.num_start_words: int = story_start_words
        self.words_per_epoch: int = story_words_per_epoch

        if create_story:
            if text is None:
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> No text is input. Cannot create story.")
                raise AIconValueError(f"No text is input. Cannot create story.")

            # overwrite epochs to match story length
            num_words: int = len(self.all_words)
            self.epochs: float = 1 + (num_words - self.num_start_words) / self.words_per_epoch

            # add one epoch if not divisible
            self.epochs: int = int(self.epochs) if int(self.epochs) == self.epochs else int(self.epochs) + 1
            if self.separator is not None:
                if self.separator not in text:
                    logger.warning(f"[{self.client_uuid}]: <<AIcon Core>> Separator `{self.separator}` will be ignored since not in text")
                    self.separator = None
                else:
                    self.epochs = len(list(filter(None,text.split(self.separator))))
            if self.separator is not None:
                logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Running for {self.epochs} epochs (split with `{self.separator}` as the separator)")
        else: 
            self.epochs = epochs

        # jit models only compatible with version CORE_COMPATIBLE_PYTORCH_VERSION
        if CORE_COMPATIBLE_PYTORCH_VERSION not in torch.__version__:
            if jit:
                logger.warning(f"[{self.client_uuid}]: <<AIcon Core>> Setting jit to False because torch version is not {CORE_COMPATIBLE_PYTORCH_VERSION}")
            jit = False

        # Load CLIP
        self.device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        clip_perceptor, norm = load(model_name, jit=jit, device=self.device)
        self.perceptor: nn.Module = clip_perceptor.eval()

        for param in self.perceptor.parameters():
            param.requires_grad = False

        if jit == False:
            input_res: int = clip_perceptor.visual.input_resolution
        else:
            input_res = clip_perceptor.input_resolution.item()
        self.clip_transform = create_clip_img_transform(input_res)
        
        self.iterations: int = iterations
        self.image_width: int = image_width
        total_batches: int = self.epochs * self.iterations * batch_size * gradient_accumulate_every

        model: DeepDaze = DeepDaze(
            self.perceptor,
            norm,
            input_res,
            total_batches,
            batch_size=batch_size,
            image_width=image_width,
            num_layers=num_layers,
            theta_initial=theta_initial,
            theta_hidden=theta_hidden,
            lower_bound_cutout=lower_bound_cutout,
            upper_bound_cutout=upper_bound_cutout,
            saturate_bound=saturate_bound,
            gauss_sampling=gauss_sampling,
            gauss_mean=gauss_mean,
            gauss_std=gauss_std,
            do_cutout=do_cutout,
            center_bias=center_bias,
            center_focus=center_focus,
            hidden_size=hidden_size,
            averaging_weight=averaging_weight,
        ).to(self.device)

        self.model: DeepDaze = model
        self.scaler: GradScaler = GradScaler()
        siren_params: Iterator[Parameter] = model.model.parameters()

        if optimizer == "AdamP":
            self.optimizer: Union[AdamP, optim.Adam, DiffGrad] = AdamP(siren_params, lr)
        elif optimizer == "Adam":
            self.optimizer = optim.Adam(siren_params, lr)
        elif optimizer == "DiffGrad":
            self.optimizer = DiffGrad(siren_params, lr)

        self.gradient_accumulate_every: int = gradient_accumulate_every
        self.text: Optional[str] = text
        self.image: Optional[str] = target_img
        self.textpath: str = create_text_path(self.perceptor.context_length, text=text, target_img=target_img, separator=story_separator)
        self.response_filename: Optional[Path] = None
        
        # create coding to optimize for
        self.clip_encoding: torch.Tensor = self.create_clip_encoding(text=text, target_img=target_img, encoding=clip_encoding)

        self.start_image: Optional[torch.Tensor] = None
        self.start_image_train_iters: int = start_image_train_iters
        self.start_image_lr: float = start_image_lr

        if source_img is not None:
            image: Image = Image.open(source_img).convert('RGB')
            start_img_transform: Compose = T.Compose([
                T.Resize(image_width),
                T.CenterCrop((image_width, image_width)),
                T.ToTensor()
            ])
            image_tensor: torch.Tensor = start_img_transform(image).unsqueeze(0).to(self.device)
            self.start_image: torch.Tensor = image_tensor
            
    def create_clip_encoding(self, text: Optional[str] = None, target_img: Optional[str] = None, encoding: Optional[torch.Tensor] = None) -> torch.Tensor:
        self.text: Optional[str] = text
        self.target_img: Optional[str] = target_img

        if encoding is not None:
            encoding = encoding.to(self.device)
        elif self.create_story:
            encoding = self.update_story_encoding()
        elif text is not None and target_img is not None:
            encoding = (self.create_text_encoding(text) + self.create_img_encoding(target_img)) / 2
        elif text is not None:
            encoding = self.create_text_encoding(text)
        elif target_img is not None:
            encoding = self.create_img_encoding(target_img)

        return encoding

    def create_text_encoding(self, text: str) -> torch.Tensor:
        tokenized_text = tokenize(text).to(self.device)

        with torch.no_grad():
            text_encoding: torch.Tensor = self.perceptor.encode_text(tokenized_text).detach()

        return text_encoding
    
    def create_img_encoding(self, target_img: str) -> torch.Tensor:
        target_img: Image = Image.open(target_img).convert('RGB')
        normed_img: torch.Tensor = self.clip_transform(target_img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            img_encoding: torch.Tensor = self.perceptor.encode_image(normed_img).detach()

        return img_encoding
    
    def set_clip_encoding(self, text: Optional[str] = None, target_img: Optional[str] = None, encoding: Optional[torch.Tensor] = None) -> torch.Tensor:
        encoding: torch.Tensor = self.create_clip_encoding(text=text, target_img=target_img, encoding=encoding)
        self.clip_encoding: torch.Tensor = encoding.to(self.device)
    
    def index_of_first_separator(self) -> int:
        for c, word in enumerate(self.all_words):
            if self.separator in str(word):
                return c + 1

    def update_story_encoding(self) -> torch.Tensor:
        if self.separator is not None:
            self.words: str = " ".join(self.all_words[:self.index_of_first_separator()])
            #removes separator from epoch-text
            self.words = self.words.replace(self.separator, '')
            self.all_words = self.all_words[self.index_of_first_separator():]
        else:
            if self.words is None:
                self.words = " ".join(self.all_words[:self.num_start_words])
                self.all_words = self.all_words[self.num_start_words:]
            else:
                # add words_per_epoch new words
                count: int = 0
                while count < self.words_per_epoch and len(self.all_words) > 0:
                    new_word = self.all_words[0]
                    self.words = " ".join(self.words.split(" ") + [new_word])
                    self.all_words = self.all_words[1:]
                    count += 1

                # remove words until it fits in context length
                while len(self.words) > self.perceptor.context_length:
                    # remove first word
                    self.words = " ".join(self.words.split(" ")[1:])

        # get new encoding
        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Now thinking of `{self.words}`")
        encoding: torch.Tensor = self.create_text_encoding(self.words)

        return encoding

    def get_output_img_path(self, sequence_number: Optional[int]) -> Tuple[Path, Path]:
        output_path: str = self.textpath
        save_output_path: str = os.path.join(self.save_img_path, f"{output_path}.{sequence_number:06d}")
        response_output_path: str = os.path.join(self.response_img_path, f"{output_path}.{sequence_number:06d}")

        return (Path(f"{save_output_path}.png"), Path(f"{response_output_path}.png"))

    def train_step(self, epoch: int, iteration: int) -> None:
        for _ in range(self.gradient_accumulate_every):
            with autocast(enabled=True):
                out: torch.Tensor
                loss: torch.Tensor
                out, loss = self.model(self.clip_encoding)
            loss = loss / self.gradient_accumulate_every
            self.scaler.scale(loss).backward()

            del loss
   
        out = out.cpu().float().clamp(0., 1.)
        self.scaler.step(self.optimizer)
        self.scaler.update()
        self.optimizer.zero_grad(set_to_none=True)

        self.save_image(epoch, iteration, img=out)
    
    def get_img_sequence_number(self, epoch: int, iteration: int) -> int:
        sequence_number: int = epoch * self.iterations + iteration

        return sequence_number

    @torch.no_grad()
    def save_image(self, epoch: int, iteration: int, img: Optional[torch.Tensor] = None) -> None:
        sequence_number: int = self.get_img_sequence_number(epoch, iteration)

        if img is None:
            img = self.model(self.clip_encoding, return_loss=False).cpu().float().clamp(0., 1.)

        save_filename, self.response_filename = self.get_output_img_path(sequence_number=sequence_number)
        
        pil_img: Image = T.ToPILImage()(img.squeeze())
        pil_img.save(save_filename)

        self.writer.append_data(np.uint8(np.array(pil_img)))

    def forward(self):
        if exists(self.start_image):
            logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Preparing with the initial image. This may take tens of seconds")
            optim = DiffGrad(self.model.model.parameters(), lr=self.start_image_lr)
            try:
                for _ in range(self.start_image_train_iters):
                    loss: torch.Tensor = self.model.model(self.start_image)
                    loss.backward()

                    optim.step()
                    optim.zero_grad(set_to_none=True)
            except KeyboardInterrupt as e:
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> Keyboard Interrunpted")
                raise e

            del self.start_image
            del optim

        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Imagining `{self.textpath}` from the depths of the weights")

        with torch.no_grad():
            self.model(self.clip_encoding, dry_run=True) # do one warmup step due to potential issue with CLIP and CUDA

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

                    logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Processing... {sequence_number + 1}/{self.iterations * self.epochs}")

                # Update clip_encoding per epoch if we are creating a story
                if self.create_story:
                    self.clip_encoding = self.update_story_encoding()

        except KeyboardInterrupt as e:
            logger.error(f"[{self.client_uuid}]: <<AIcon Core>> Keyboard Interrunpted")
            raise e

        except RuntimeError as e:
            if 'out of memory' in str(e):
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> Ran out of gpu memory")
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

            logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Completed imagination")
