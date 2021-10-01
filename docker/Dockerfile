FROM pytorch/pytorch:1.7.1-cuda11.0-cudnn8-devel

RUN sed -i.bak -e "s%http://[^ ]\+%http://ftp.jaist.ac.jp/pub/Linux/ubuntu/%g" /etc/apt/sources.list

ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics
ENV DEBIAN_FRONTEND noninteractive

LABEL maintainer="magic_spell"

SHELL ["/bin/bash", "-c"]

ARG WORK_DIR="/workspace"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sudo \
        gosu \
        build-essential \
        pkg-config \
        apt-utils \
        bash-completion \
        command-not-found \
        git \
        curl \
        wget \
        less \
        nano \
        tmux \
        unzip \
        libfontconfig \
        libappindicator1 \
        fonts-liberation \
        libasound2 \
        libnspr4 \
        libnss3 \
        libxss1 \
        lsb-release \
        xdg-utils \
        libfreetype6-dev \
        libxft-dev \
        libjpeg62 \
        libjpeg-dev \
        ffmpeg \
        software-properties-common \
        xdg-user-dirs \
        xsel \
        dirmngr \
        gpg-agent \
        mesa-utils \
        libglu1-mesa-dev \
        libgles2-mesa-dev \
        freeglut3-dev \
        libcanberra-gtk-module \
        libcanberra-gtk3-module \
        python3-pip \
        python3-dev \
        gfortran \
        libopenblas-dev \
        libhdf5-serial-dev \
        libhdf5-dev \
        zlib1g-dev \
        zip \
        libpng-dev \
        libfreetype6-dev \
        libopenmpi-dev \
        zlib1g-dev \
        locales \
        libjpeg8-dev \
        libgconf-2-4 \
        libnss3-dev && \
    apt-get --fix-broken install && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p ${WORK_DIR}

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb

RUN echo "PYTHONIOENCODING=utf-8" >> /root/.bashrc && \
    echo "TF_CPP_MIN_LOG_LEVEL=2" >> /root/.bashrc && \
    echo "export PS1='\[\033[01;32m\]pytorch@docker\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> /root/.bashrc

RUN pip3 install --verbose \
        setuptools \
        Cython \
        wheel \
        numpy \
        future==0.17.1 \
        mock==3.0.5 \
        gast==0.2.2 \
        futures \
        protobuf \
        pybind11 \
        six \
        cycler \
        kiwisolver \
        pyparsing \
        python-dateutil \
        Pillow \
        opencv-contrib-python==4.4.0.46 \
        Flask \
        flask-cors \
        flask_limiter \
        flask_restful \
        waitress \
        bs4 \
        webdriver-manager \
        selenium \
        googletrans==4.0.0-rc1 \
        siren_pytorch \
        torch_optimizer \
        boto3 \
        ftfy \
        regex \
        tweepy \
        imageio \
        imageio_ffmpeg

RUN locale-gen ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL=ja_JP.UTF-8
RUN localedef -f UTF-8 -i ja_JP ja_JP.utf8

WORKDIR /workspace

RUN adduser --disabled-password --gecos '' --shell /bin/bash user && \
    chown -R user:user /workspace && \
    mkdir -p /etc/sudoers.d/
RUN echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-user
USER user

ENV HOME=/home/user
RUN chmod 777 /home/user
ARG HOSTNAME="aicon"
RUN echo "export PS1='\[\033[01;32m\]aicon@${HOSTNAME}\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '" >> /home/user/.bashrc && \
    echo "PYTHONIOENCODING=utf-8" >> /home/user/.bashrc && \
    echo 'alias python="python3"' >> /home/user/.bashrc && \
    echo 'alias pip="pip3"' >> /home/user/.bashrc

RUN mkdir ${HOME}/.cache && \
    cd ${HOME}/.cache && \
    wget --progress=dot https://openaipublic.azureedge.net/clip/models/afeb0e10f9e5a86da6080e35cf09123aca3b358a0c3e3b6c78a7b63bc04b6762/RN50.pt && \
    wget --progress=dot https://openaipublic.azureedge.net/clip/models/8fa8567bab74a42d41c5915025a8e4538c3bdbe8804a470a72f30b0d94fab599/RN101.pt && \
    wget --progress=dot https://openaipublic.azureedge.net/clip/models/7e526bd135e493cef0776de27d5f42653e6b4c8bf9e0f653bb11773263205fdd/RN50x4.pt && \
    wget --progress=dot https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-128-pytorch_model.bin && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-256-pytorch_model.bin && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-512-pytorch_model.bin && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-128-config.json && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-256-config.json && \
    wget --progress=dot https://s3.amazonaws.com/models.huggingface.co/biggan/biggan-deep-512-config.json

ENV DEBIAN_FRONTEND=newt
