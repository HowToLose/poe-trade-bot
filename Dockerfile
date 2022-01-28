FROM python:3.9-slim

WORKDIR /poe-trade-bot
COPY . /poe-trade-bot
RUN pip install -r requirements.txt