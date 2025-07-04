FROM python:3.13.2-slim-bookworm

ADD . /MedChain

WORKDIR /MedChain

RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSf https://raw.githubusercontent.com/solana-labs/solana/v1.10.0/install/solana-install-init.sh | sh -s - v1.10.0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["./entrypoint.sh"]
