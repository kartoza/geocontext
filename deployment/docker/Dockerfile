FROM python:3.8-slim-buster

LABEL maintainer="Andre Theron<andre.theron@kartoza.com>"

RUN DEBIAN_FRONTEND=noninteractive \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
    binutils \
    gcc \
    gdal-bin \
    git \
    libproj-dev \
    libgdal-dev \
    python3-gdal \
    python3-geoip \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /etc/geocontext/requirements.txt
RUN pip3 install --upgrade pip setuptools \
    && pip3 install --no-cache-dir -r /etc/geocontext/requirements.txt

EXPOSE 8080
WORKDIR /usr/src/geocontext
COPY uwsgi.conf /etc/geocontext/
CMD ["uwsgi", "--ini", "/etc/geocontext/uwsgi.conf"]