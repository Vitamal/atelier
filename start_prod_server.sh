#!/bin/sh
python manage.py collectstatic --noinput &&
daphne atelier.asgi:application -b 0.0.0.0 -p $PORT --proxy-headers &
python manage.py rqworker