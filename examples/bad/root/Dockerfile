FROM ubuntu:latest
WORKDIR app
RUN apt-get update
RUN apt-get install -y curl
RUN chmod -R 777 /app
USER root
CMD python app.py
