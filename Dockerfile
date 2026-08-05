FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY cloudflare_wallet_checker ./cloudflare_wallet_checker

RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 checker
RUN mkdir -p /app/data && chown -R checker:checker /app

USER checker

CMD ["cfwallet-bot"]
