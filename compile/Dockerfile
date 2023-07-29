# Define custom function directory
#ARG FUNCTION_DIR="/code_automation"
ARG FUNCTION_DIR="/tm"

FROM python:3.8 as build-image

RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}
RUN ls ${FUNCTION_DIR}

# Install the function's dependencies
RUN pip install \
    --target ${FUNCTION_DIR} \
        awslambdaric

# Use a slim version of the base Python image to reduce the final image size
FROM python:3.8
#FROM 134622832812.dkr.ecr.us-west-2.amazonaws.com/ubuntu:20.04



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
#ENV HOME=/tmp


# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "compile.handler" ]
