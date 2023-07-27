FROM 134622832812.dkr.ecr.us-west-2.amazonaws.com/ubuntu:20.04
LABEL maintainer="yang.li@protagolabs.com"


RUN apt-get update && apt-get install -y --no-install-recommends --force-yes \
  build-essential \
  wget \
  git \
  git-lfs \
  vim \
  && apt-get clean autoclean && rm -rf /var/lib/apt/lists/{apt,dpkg,cache,log} /tmp/* /var/tmp/*

RUN git lfs install

RUN wget --no-check-certificate https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O install_miniconda.sh && \
bash install_miniconda.sh -b -p /opt/conda && rm install_miniconda.sh
ENV PATH="/opt/conda/bin:${PATH}"
ENV PYTHONHOME="/opt/conda"

RUN conda install python==3.8 pip && \
    conda clean --all

COPY ./* /src/
WORKDIR /src/

RUN pip install -r requirements.txt
ENTRYPOINT ["python","hello.py"]



