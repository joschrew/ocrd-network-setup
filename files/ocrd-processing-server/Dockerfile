FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# install dependencies
RUN apt-get update && apt-get -y install \
    git \
    curl \
    make \
    vim \
    python3 \
    python3-pip

RUN mkdir /repos && \
	cd /repos &&  \
	git clone https://github.com/ocr-d/core.git && \
	cd core && \
	git checkout processor-server && \
	make deps-ubuntu && \
	make install
