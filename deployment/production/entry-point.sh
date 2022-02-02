#!/usr/bin/env bash

echo "Run database migrations"
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Run collectstatic
echo "Run collectstatic"
python manage.py collectstatic --noinput

# Run as bash entrypoint
exec "$@"
