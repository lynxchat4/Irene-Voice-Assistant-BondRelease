# syntax=docker/dockerfile:1
FROM node:16.13.0-alpine AS frontend-builder

WORKDIR /home/frontend

COPY ./frontend/package*.json ./
RUN npm ci

COPY ./frontend .
RUN npm run build

FROM curlimages/curl:7.85.0 as silero-downloader

WORKDIR /home/downloader/models

RUN curl https://models.silero.ai/models/tts/ru/v3_1_ru.pt -o ./c9e311e020562111e5414ff93d47e0a1-v3_1_ru.pt

FROM curlimages/curl:7.85.0 as vosk-downloader

WORKDIR /home/downloader/models

RUN curl https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip -o ./c611af587fcbdacc16bc7a1c6148916c-vosk-model-small-ru-0.22.zip

FROM python:3.9-slim-bullseye as ssl-generator

WORKDIR /home/generator/ssl

RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -nodes -days 365 -subj "/C=RU/CN=*"

FROM python:3.9-slim-bullseye

RUN useradd --create-home python
USER python:python
WORKDIR /home/python

COPY ./requirements-docker.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY irene ./irene
COPY irene_plugin_web_face ./irene_plugin_web_face
COPY irene_plugin_web_face_frontend ./irene_plugin_web_face_frontend
COPY docker-config ./config

COPY --link --from=frontend-builder /home/frontend/dist/ ./irene_plugin_web_face_frontend/frontend-dist/
COPY --link --from=silero-downloader /home/downloader/models/ ./silero-models/
COPY --link --from=vosk-downloader /home/downloader/models/ ./vosk-models/
COPY --link --chown=python:python --from=ssl-generator /home/generator/ssl/ ./ssl/

EXPOSE 8086

VOLUME /irene
ENV IRENE_HOME=/irene

ENTRYPOINT ["python", "-m", "irene", "--default-config", "/home/python/config"]
