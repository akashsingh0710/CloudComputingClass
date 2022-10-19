FROM debian:11-slim

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
EXPOSE 8005
COPY modelTest.py /app/modelTest.py
CMD [ "python3", "./modelTest.py"]