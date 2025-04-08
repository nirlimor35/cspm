FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /cspm
WORKDIR /cspm

COPY providers/ providers/
COPY utils/ utils/
COPY cspm.py .
COPY main.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt --break-system-packages && \
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin && \
    chmod +x utils/docker_install.sh && \
    ./utils/docker_install.sh && \
    chmod +x cspm.py

RUN useradd -m cspm && \
    groupadd -f docker && \
    usermod -aG docker cspm && \
    chown -R cspm:cspm /cspm

USER cspm

CMD ["python3", "cspm.py"]
