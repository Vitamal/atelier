FROM python:3.7-alpine

ENV PYTHONBUFFERED 1

RUN apk --update add libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc openssl-dev curl
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev
RUN pip install Pillow

#RUN apt-get update && apt-get install -f -y netcat
RUN apk update \
    && apk add build-base pkgconfig python3-dev openssl-dev libxml2-dev libxslt-dev libffi-dev musl-dev make gcc postgresql-dev\
    && pip install psycopg2

RUN mkdir requirements
COPY requirements/develop.txt /requirements/
COPY requirements/common.txt /requirements/
RUN pip install -r requirements/develop.txt

RUN mkdir /web
WORKDIR /web

ADD . /web/