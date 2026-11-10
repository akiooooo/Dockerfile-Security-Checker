FROM python:3.12-slim
WORKDIR /app
COPY --chown=10001:10001 app.py /app/app.py
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080', timeout=2)"]
CMD ["python", "/app/app.py"]
