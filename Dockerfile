FROM ubuntu:noble
#FROM python:3.13-alpine

RUN apt-get update -y
RUN apt-get install pip curl -y

RUN mkdir /cspm
COPY providers cspm/providers/
COPY utils cspm/utils/
COPY ./cspm.py /cspm
COPY ./main.py /cspm
COPY ./requirements.txt /cspm

RUN pip3 install -r /cspm/requirements.txt --break-system-packages
# Installing grype ->
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
RUN chmod +x /cspm/utils/docker_install.sh
RUN ./cspm/utils/docker_install.sh
WORKDIR /cspm
RUN chmod +x /cspm/cspm.py

CMD ["python3", "/cspm/cspm.py"]