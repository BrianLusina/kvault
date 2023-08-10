FROM python:3.10.5-slim

WORKDIR /tmp

ARG CONTAINER_USER_NAME=kvault
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN set -x \
    && addgroup --system ${CONTAINER_USER_NAME} || true \
    && adduser --system --ingroup ${CONTAINER_USER_NAME} --home /home/${CONTAINER_USER_NAME} --gecos "${CONTAINER_USER_NAME} user" --shell /bin/false  ${CONTAINER_USER_NAME}

COPY . .

RUN pip install poetry
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip install -r requirements.txt --no-cache-dir

USER $CONTAINER_USER_NAME

EXPOSE 31337

VOLUME /var/lib/kvault

ENTRYPOINT ["python", "cli.py", "-l", "/var/lib/kvault/server.log", "-H", "0.0.0.0"]
