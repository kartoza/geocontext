FROM python:3.8-buster

LABEL maintainer="Dimas Ciputra<dimas@kartoza.com>"
LABEL maintainer="Andre Theron<andre.theron@kartoza.com>"

RUN export DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND noninteractive
RUN dpkg-divert --local --rename --add /sbin/initctl

RUN apt-get update -y && apt-get install -y \
    binutils gdal-bin \
    libproj-dev \
    libgdal-dev \
    python3-gdal \
    python3-geoip \
    python3-setuptools \
    uwsgi-plugin-python3 \
    && rm -rf /var/lib/apt/lists/*
 
ADD REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip3 install --upgrade pip && pip3 install -r /REQUIREMENTS.txt

ADD uwsgi.conf /uwsgi.conf

EXPOSE 8080

WORKDIR /usr/src/geocontext

CMD ["uwsgi", "--ini", "/uwsgi.conf"]