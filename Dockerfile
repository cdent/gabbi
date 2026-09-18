FROM python:3-alpine
MAINTAINER Chris Dent <cdent@anticdent.org>

ARG GABBI_VERSION
RUN python -m venv /app
RUN mkdir buildgabbi
COPY . /buildgabbi/
RUN cd /buildgabbi && /app/bin/pip --no-cache-dir install .

ENTRYPOINT ["/app/bin/python", "-m", "gabbi.runner"]
