FROM python:3.6.1

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

