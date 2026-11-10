FROM alpine:3.21 AS base
RUN apk add --no-cache ca-certificates
USER 10001:10001
HEALTHCHECK CMD ["true"]

FROM base AS runtime
WORKDIR /app
CMD ["true"]
