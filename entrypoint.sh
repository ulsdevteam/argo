#!/bin/bash

./wait-for-it.sh db:5432 -- echo "Running entrypoint.sh"

if [ ! -f manage.py ]; then
  cd argo
fi

if [ ! -f argo/config.py ]; then
    cp argo/config.py.example argo/config.py
fi

echo "Apply database migrations"
python manage.py migrate

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
