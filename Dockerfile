FROM alpine:3.18.2

WORKDIR /tmp

RUN apk add --no-cache --virtual .build-deps build-base python3-dev \
      && apk add --no-cache libev python3 py3-pip \
      && pip3 install --no-cache-dir gevent simpledb \
      && apk del .build-deps

EXPOSE 31337

VOLUME /var/lib/kvault

ENTRYPOINT ["kvault.py", "-l", "/var/lib/kvault/server.log", "-H", "0.0.0.0"]
