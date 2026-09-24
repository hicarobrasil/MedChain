FROM python:3.11-buster

ADD ./medchain

WORKDIR /medchain

RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSf https://raw.githubusercontent.com/solana-labs/solana/v1.10.0/install/solana-install-init.sh | sh -s - v1.10.0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"
ENV PYTHONPATH="/app:${PYTHONPATH}"
RUN chmod +x entrypoint.sh

ENTRYPOINT [".entrypoint.sh"]
