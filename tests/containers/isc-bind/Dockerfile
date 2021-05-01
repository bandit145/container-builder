# Fake docker file because I am 100% not actually building bind as a test
FROM docker.io/alpine:latest
RUN apk update && apk add git
COPY ./build-dir/ build-dir
# RUN apk add gcc libuv pkgconfig autoconf automake libtool musl-dev make perl-pod-coverage perl-doc
# RUN apk add libxml2 openssl openssl-dev libcap libcap-dev nghttp2 libuv libuv-dev
# RUN cd build-dir/ && autoreconf -fi && ./configure && make
ENTRYPOINT yes


# FROM docker.io/alpine:latest
