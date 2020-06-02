FROM python:3.8-buster

LABEL maintainer="Dimas Ciputra<dimas@kartoza.com>"
LABEL maintainer="Andre Theron<andre.theron@kartoza.com>"

RUN export DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND noninteractive
RUN dpkg-divert --local --rename --add /sbin/initctl

RUN apt-get update --fix-missing -y \
    && apt-get upgrade -y  \
    && apt-get install -y python3-gdal uwsgi-plugin-python3

ADD REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip3 install --upgrade pip && pip install -r /REQUIREMENTS.txt

ADD uwsgi.conf /uwsgi.conf

EXPOSE 8080

WORKDIR /usr/src/geocontext

CMD ["uwsgi", "--ini", "/uwsgi.conf"]