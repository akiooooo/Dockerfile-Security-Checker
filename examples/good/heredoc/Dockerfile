# syntax=docker/dockerfile:1
FROM alpine:3.21
RUN <<EOF
echo "The word FROM here is just text"
apk add --no-cache ca-certificates
EOF
USER 10001
CMD ["true"]
