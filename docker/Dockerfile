FROM nvcr.io/nvidia/pytorch:21.08-py3

RUN sed -i.bak -e "s%http://[^ ]\+%http://ftp.jaist.ac.jp/pub/Linux/ubuntu/%g" /etc/apt/sources.list

ENV NVIDIA_VISIBLE_DEVICES ${NVIDIA_VISIBLE_DEVICES:-all}
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES:+$NVIDIA_DRIVER_CAPABILITIES,}graphics

LABEL maintainer="sudo_rm-rf_/"
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y \
        sudo \
        wget \
        curl \
        unzip \
        apt-utils \
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
        nano \
        locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/root/src && cd $_ && \
    touch /etc/default/google-chrome && \
    wget -O /tmp/chromedriver.zip \
        http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ && \
    apt-get update && \
    apt-get install -y \
        libgconf-2-4 \
        libnss3-dev \
        libxss1 && \
    apt-get --fix-broken install && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb

RUN pip3 install \
        flask-cors \
        waitress \
        bs4 \
        chromedriver-binary \
        selenium \
        googletrans==4.0.0-rc1

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

ENV DEBIAN_FRONTEND=newt
