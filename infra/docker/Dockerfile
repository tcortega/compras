FROM alpine:3.20

RUN apk add --no-cache iptables iptables-legacy iproute2 jq

COPY ensure-icc.sh /ensure-icc.sh
RUN chmod +x /ensure-icc.sh

ENTRYPOINT ["/bin/sh", "/ensure-icc.sh"]
