FROM continuumio/miniconda3:24.5.0-0
LABEL authors="edwardbird"

RUN apt update && apt install build-essential git -y && apt clean && rm -rf /var/lib/apt/lists/*
WORKDIR /work
#COPY ./* .
RUN git clone https://github.com/edwardbirdlab/rgi.git
WORKDIR /work/rgi
RUN conda env create -f ./conda_env.yml
RUN echo "source activate rgi" > ~/.bashrc
#RUN pip install git+https://github.com/edwardbirdlab/rgi.git
RUN python setup.py build
RUN python setup.py test
RUN python setup.py install

ENV PATH /opt/conda/envs/rgi/bin:$PATH

ENTRYPOINT ["rgi"]