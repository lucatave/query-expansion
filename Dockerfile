FROM python:3.6.1

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN python -m nltk.downloader -d /data/nltk_data wordnet

COPY . .
