FROM python:3.7-alpine

ENV PYTHONBUFFERED 1

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