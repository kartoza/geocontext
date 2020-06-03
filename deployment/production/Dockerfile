FROM python:3.8-buster

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

ARG BRANCH
RUN git clone --depth=1 git://github.com/kartoza/geocontext.git --branch ${BRANCH} /usr/src/geocontext

WORKDIR /usr/src/geocontext

RUN mkdir -p /home/web/media
ADD entry-point.sh /usr/src/geocontext/entry-point.sh
RUN chmod +x /usr/src/geocontext/entry-point.sh

ADD uwsgi.conf /usr/src/geocontext/uwsgi.conf

EXPOSE 8080

ENTRYPOINT ["/usr/src/geocontext/entry-point.sh"]
CMD ["uwsgi", "--ini", "/usr/src/geocontext/uwsgi.conf"]