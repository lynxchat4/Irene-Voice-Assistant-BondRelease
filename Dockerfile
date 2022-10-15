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

FROM python:3.9-slim-bullseye

WORKDIR /home/python

COPY ./requirements-docker.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY irene ./irene
COPY irene_plugin_web_face ./irene_plugin_web_face
COPY irene_plugin_web_face_frontend ./irene_plugin_web_face_frontend
COPY docker-config ./config

COPY --link --from=frontend-builder /home/frontend/dist/ ./irene_plugin_web_face_frontend/frontend-dist/
COPY --link --from=silero-downloader /home/downloader/models/ ./silero-models/

EXPOSE 8086

CMD ["python", "-m", "irene", "--default-config", "/home/python/config"]
