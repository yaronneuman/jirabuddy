FROM ubuntu:18.04

RUN apt upgrade && apt update && apt install -y curl libffi-dev libssl-dev python3 python3-pip
COPY requirements.txt /opt/app/requirements.txt
RUN pip3 install -v -r /opt/app/requirements.txt

ARG CA_BUNDLE
ARG CONFIGURATION_FILE=./configuration_template.yaml
ARG PLUGINS_FILE=./example_plugins.py

COPY ./ /opt/app/
COPY ${CA_BUNDLE} /opt/app/ca-bundle.pem
COPY ${CONFIGURATION_FILE} /opt/app/.config/colo/config.yaml
COPY ${PLUGINS_FILE} /opt/app/colo_plugins.py

VOLUME ["/opt/app"]
WORKDIR /opt/app

ENV WEBSOCKET_CLIENT_CA_BUNDLE="/opt/app/ca-bundle.pem"
ENV CURL_CA_BUNDLE="/opt/app/ca-bundle.pem"
ENV HOME="/opt/app/"
ENTRYPOINT ["python3", "main.py"]


