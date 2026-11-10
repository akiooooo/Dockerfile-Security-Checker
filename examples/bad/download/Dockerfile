FROM alpine
RUN wget --no-check-certificate https://example.invalid/install.sh -O - | sh
ADD https://example.invalid/archive.tar.gz /app/
USER 10001
CMD ["true"]
