FROM python:3.12-slim
WORKDIR /app
COPY dockercheck ./dockercheck
USER 10001:10001
ENTRYPOINT ["python", "-m", "dockercheck"]
CMD ["--help"]
