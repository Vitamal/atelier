#!/bin/bash

set -e

#waiting for postgres
until $(nc -z ${DB_HOST} ${DB_PORT})
do
  echo "Waiting for PostgreSQL..."
  echo "${DB_HOST}-${DB_PORT}"
  sleep 3
done

python manage.py migrate
#python manage.py collectstatic
#python manage.py loaddata development_database.json
#python manage.py rqworker &
python manage.py runserver 0.0.0.0:8000
