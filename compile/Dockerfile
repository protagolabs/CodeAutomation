# Define custom function directory
#ARG FUNCTION_DIR="/code_automation"
ARG FUNCTION_DIR="/code_automation"

FROM python:3.10 as build-image

   

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}

# Install the function's dependencies
RUN pip install \
    --target ${FUNCTION_DIR} \
        awslambdaric

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.10


# RUN apt-get update && apt-get install -y --no-install-recommends --force-yes \
#   build-essential \
#   wget \
#   git \
#   git-lfs \
#   vim \
#   && apt-get clean autoclean && rm -rf /var/lib/apt/lists/{apt,dpkg,cache,log} /tmp/* /var/tmp/*
# RUN git lfs install

# RUN wget --no-check-certificate https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O install_miniconda.sh && \
# bash install_miniconda.sh -b -p /opt/conda && rm install_miniconda.sh

# ENV PATH="/opt/conda/bin:${PATH}"
# RUN conda install python==3.10 pip && \
#     conda clean --all
# ENV PYTHONHOME="/opt/conda"


# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

RUN pip install -r requirements.txt
# Aws container forbid user write data except directory /tmp, nuitka will  generate ccache directory in /home/user default
# https://github.com/Nuitka/Nuitka/blob/develop/nuitka/utils/AppDirs.py#L50
# so we should set NUITKA_CACHE_DIR to director /tmp

ENV NUITKA_CACHE_DIR=/tmp


# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "compile.handler" ]
