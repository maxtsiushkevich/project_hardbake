FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY api/ ./api/

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8004

CMD ["python", "-m", "api.main"]