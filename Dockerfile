FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y \
    autoconf \
    libtool \
    libffi-dev \
    mc \
    vim \
    build-essential \
    tzdata \
    openjdk-17-jdk \
    libopencv-dev \
    zip \
    unzip \
    curl \
    git \ 
    libncursesw5-dev \
    libssl-dev \
    libsqlite3-dev \
    tk-dev \
    libgdbm-dev \
    libc6-dev \
    libbz2-dev \
    sudo \
    cmake
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN usermod --shell /bin/bash docker
USER docker
RUN mkdir -p /home/docker/code
WORKDIR "/home/docker/code"
RUN git clone https://github.com/ssppkenny/pyflow-android.git
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
ENV PATH=$JAVA_HOME/bin:$PATH
CMD ["/bin/sh", "-c", "bash"]

