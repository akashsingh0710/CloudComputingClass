FROM debian:10.3-slim

WORKDIR /app

RUN apt-get update && apt-get -y dist-upgrade

RUN apt-get -y install apt-utils \
    build-essential \
    python3 \
    gcc \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-pandas

ADD requirements.txt .
RUN pip3 install -r requirements.txt
ENV FLASK_ENV=development
EXPOSE 6001
COPY bigram.py /app/bigram.py
CMD [ "python3", "./bigram.py"]