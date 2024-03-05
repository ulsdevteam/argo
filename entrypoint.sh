#!/bin/bash

if [ ! -f manage.py ]; then
  cd argo
fi

if [ ! -f argo/config.py ]; then
    if [[ -n $PROD ]]; then
      envsubst < argo/config.py.deploy > argo/config.py
    else
      cp argo/config.py.example argo/config.py
    fi
fi

./wait-for-it.sh $db:${SQL_PORT} -- echo "Running entrypoint.sh"

echo "Apply database migrations"
python manage.py migrate

#Start server
echo "Starting server"
if [[ -n $PROD ]]; then
    # Collect static files
    echo "Collecting static files"
    python manage.py collectstatic

    chmod 775 /var/www/html/argo/static
    chown www-data:www-data /var/www/html/argo/static
    apache2ctl -D FOREGROUND
else
    python manage.py runserver 0.0.0.0:${APPLICATION_PORT}
fi
