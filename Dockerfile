FROM python:3.11-buster

WORKDIR /medchain

RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSf https://raw.githubusercontent.com/solana-labs/solana/v1.10.0/install/solana-install-init.sh | sh -s - v1.10.0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH="/root/.local/share/solana/install/active_release/bin:${PATH}"
ENV PYTHONPATH="/medchain:${PYTHONPATH}"
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
