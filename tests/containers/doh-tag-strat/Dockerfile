FROM docker.io/golang:1.15.8 AS builder
COPY build-dir build-dir
RUN cd build-dir/ && make


FROM docker.io/alpine:latest
RUN mkdir /etc/doh-server/ && mkdir /lib64 && ln -s /lib/libc.musl-x86_64.so.1 /lib64/ld-linux-x86-64.so.2
VOLUME /etc/doh-server/
COPY --from=builder /go/dns-over-https/doh-server/doh-server /bin/doh-server
RUN chmod +x /bin/doh-server
COPY --from=builder /go/dns-over-https/doh-server/doh-server.conf /etc/doh-server/
ENTRYPOINT /bin/doh-server -conf /etc/doh-server/doh-server.conf -verbose