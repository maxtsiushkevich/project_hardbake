FROM python:3.12-alpine as builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-alpine

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY api/ ./api/

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

CMD ["python", "-m", "api.main"]