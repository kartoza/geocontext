#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
# Note this base image is based on debian
FROM python:3.6.8
MAINTAINER Dimas Ciputra<dimas@kartoza.com>

RUN export DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND noninteractive
RUN dpkg-divert --local --rename --add /sbin/initctl

RUN apt-get update -y

RUN apt-get install -y python3-pip \
    python-gdal \
    python-geoip \
    python3-setuptools

ADD REQUIREMENTS.txt /REQUIREMENTS.txt
RUN pip install -r /REQUIREMENTS.txt
RUN pip install uwsgi

ARG BIMS_TAG=develop
RUN git clone --depth=1 git://github.com/kartoza/geocontext.git --branch ${BIMS_TAG} /usr/src/geocontext

#USER www-data
WORKDIR /usr/src/geocontext

RUN mkdir -p /home/web/media
ADD entry-point.sh /usr/src/geocontext/entry-point.sh
RUN chmod +x /usr/src/geocontext/entry-point.sh

ADD uwsgi.conf /usr/src/geocontext/uwsgi.conf

# Open port 8080 as we will be running our uwsgi socket on that
EXPOSE 8080

ENTRYPOINT ["/usr/src/geocontext/entry-point.sh"]
CMD ["uwsgi", "--ini", "/usr/src/geocontext/uwsgi.conf"]
