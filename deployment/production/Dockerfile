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
RUN pip3 install --upgrade pip && install -r /REQUIREMENTS.txt

RUN git clone --depth=1 git://github.com/kartoza/geocontext.git --branch ${BRANCH} /usr/src/geocontext

WORKDIR /usr/src/geocontext

RUN mkdir -p /home/web/media
ADD entry-point.sh /usr/src/geocontext/entry-point.sh
RUN chmod +x /usr/src/geocontext/entry-point.sh

ADD uwsgi.conf /usr/src/geocontext/uwsgi.conf

EXPOSE 8080

ENTRYPOINT ["/usr/src/geocontext/entry-point.sh"]
CMD ["uwsgi", "--ini", "/usr/src/geocontext/uwsgi.conf"]