#!/bin/bash
source /var/app/venv/*/bin/activate
export PYTHONPATH=/var/app/venv/staging-LQM1lest/bin:/var/app/staging/tabbycat
export DJANGO_SETTINGS_MODULE=settings
python manage.py migrate_schemas --noinput
