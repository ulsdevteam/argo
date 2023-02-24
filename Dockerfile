FROM python:3.10

ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install --yes apache2 apache2-dev
# RUN apt-get install --yes libapache2-mod-wsgi-py3
RUN apt-get install --yes postgresql
RUN apt-get install --yes python3-pip
RUN pip install --upgrade pip
# RUN pip install django

RUN wget https://github.com/GrahamDumpleton/mod_wsgi/archive/refs/tags/4.9.0.tar.gz \
    && tar xvfz 4.9.0.tar.gz \
    && cd mod_wsgi-4.9.0 \
    && ./configure --with-apxs=/usr/bin/apxs --with-python=/usr/local/bin/python3 \
    && make \
    && make install \
    && make clean

ADD ./apache/000-argo.conf /etc/apache2/sites-available/000-argo.conf
ADD ./apache/wsgi.load /etc/apache2/mods-available/wsgi.load
RUN a2ensite 000-argo.conf
RUN a2enmod headers
RUN a2enmod rewrite
RUN a2enmod wsgi

RUN mkdir -p /var/www/html/
COPY . /var/www/html/argo
WORKDIR /var/www/html/argo
RUN pip install -r requirements.txt
RUN ./manage.py collectstatic

RUN chmod 775 /var/www/html/argo
RUN chown :www-data /var/www/html/argo
RUN chmod 775 /var/www/html/argo/static
RUN chown :www-data /var/www/html/argo/static

EXPOSE 8001 9200
CMD ["apache2ctl", "-D", "FOREGROUND"]
