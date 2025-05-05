FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    git \
    swi-prolog \
    sfst \
    unzip \
    wget \
    python3 \
    python3-pexpect \
    python3-flask \
    python-is-python3

ADD https://api.github.com/repos/triceratopsandbottoms/ParZu/git/refs/heads/master version.json
RUN git clone https://github.com/triceratopsandbottoms/ParZu.git

RUN (cd ParZu; bash install.sh)

CMD ["python3", "/ParZu/parzu_server.py", "--host", "0.0.0.0"]
