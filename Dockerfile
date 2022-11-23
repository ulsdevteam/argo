FROM python:3.10

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN \
  apt-get install libpq-dev && \
  pip install --upgrade pip && pip install -r requirements.txt
ADD . /code/
