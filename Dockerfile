FROM python:3-alpine
MAINTAINER Chris Dent <cdent@anticdent.org>

ARG GABBI_VERSION
RUN python -m venv /app
COPY . /app/
RUN cd /app && PBR_VERSION=${GABBI_VERSION} /app/bin/pip --no-cache-dir install .

ENTRYPOINT ["/app/bin/python", "-m", "gabbi.runner"]
