FROM python:3.13-slim

RUN pip install --no-cache-dir gradio==6.14.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp
WORKDIR /workspace
USER 65534:65534
