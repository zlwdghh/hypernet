ARG cuda_version=10.0

FROM hub.kplabs.pl/cudaconda:${cuda_version}.1-runtime

ADD environment.yml environment.yml
RUN conda env update -f environment.yml

# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "decent", "/bin/bash", "-c"]

# Install CUDnn
RUN wget -O cudnn-10.0-linux-x64-v7.4.1.5.tgz -nv "https://jug.kplabs.pl/file/kUvED8duLU/iV9OSru55E"
RUN tar -xzvf cudnn-10.0-linux-x64-v7.4.1.5.tgz
RUN mkdir usr/local/cuda-10.0/include
RUN cp -P cuda/include/cudnn.h usr/local/cuda-10.0/include
RUN cp -P cuda/lib64/libcudnn* usr/local/cuda-10.0/lib64
RUN chmod a+r usr/local/cuda-10.0/include/cudnn.h /usr/local/cuda-10.0/lib64/libcudnn*

# Download DNNDK and install it
RUN wget -O xilinx_dnndk_v3.1.tar.gz -nv "https://jug.kplabs.pl/file/cZfqhhaqYz/I53ZXbZyA1"
RUN tar -xf xilinx_dnndk_v3.1.tar.gz && rm -rf xilinx_dnndk_v3.1.tar.gz
RUN pip install xilinx_dnndk_v3.1/host_x86/decent-tf/ubuntu18.04/tensorflow_gpu-1.12.0-cp36-cp36m-linux_x86_64.whl
RUN cd xilinx_dnndk_v3.1/host_x86 && ./install.sh
RUN apt-get -y update && apt-get install -y --force-yes libgomp1 jq

# Create workspace
RUN mkdir /workspace
WORKDIR /workspace

ADD ml_intuition ml_intuition
ADD scripts scripts
ADD tests tests
ADD datasets datasets
VOLUME "/workspace/parameters"

ENV PARAMETERS_DIR "/workspace/parameters"
ENV WORK_DIR "/workspace/work"

ENV PATH /opt/conda/envs/decent/bin:$PATH

ENTRYPOINT ["/bin/bash", "-c"]
