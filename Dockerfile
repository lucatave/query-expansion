FROM python:3.6.1

RUN mkdir /data

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN python -m nltk.downloader -d /data/nltk_data wordnet stopwords punkt averaged_perceptron_tagger

COPY . .
