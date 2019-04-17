ARG PYTHON_VER=3.6
ARG ETCD_VER=v3.3.12

FROM python:${PYTHON_VER}

ENV DOCKER_CHANNEL stable
ENV DOCKER_VERSION 18.09.5
ENV dockerArch x86_64
ENV ETCD_VER ${ETCD_VER:-v3.3.12}

RUN wget -O docker.tgz "https://download.docker.com/linux/static/${DOCKER_CHANNEL}/${dockerArch}/docker-${DOCKER_VERSION}.tgz" && \
    tar xvzf docker.tgz && \
    cp docker/docker /usr/bin/

RUN wget -O etcd.tgz https://github.com/etcd-io/etcd/releases/download/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz && \
    tar xvzf etcd.tgz && \
    cp  etcd-${ETCD_VER}-linux-amd64/etcdctl /usr/bin/


WORKDIR /etcd3

COPY requirements*.txt /etcd3/
RUN pip install -r requirements_dev_py3.txt

COPY . /etcd3/

RUN python ./setup.py install

CMD pytest -s -v
