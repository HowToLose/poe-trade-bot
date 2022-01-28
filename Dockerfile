FROM python:3.9-slim
RUN apt-get update
RUN apt-get -y install gcc

WORKDIR /poe-trade-bot
COPY . /poe-trade-bot
RUN pip install -r requirements.txt