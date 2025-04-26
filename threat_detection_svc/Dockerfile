FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    g++ \
    make \
    libstdc++ \
    openblas-dev

# Install libgomp explicitly
RUN apk add --no-cache libgomp

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache \
    libstdc++ \
    openblas \
    libgomp

COPY --from=builder /root/.local /root/.local
COPY api/ ./api/

ENV PATH=/root/.local/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib

EXPOSE 8005

CMD ["python", "-m", "api.main"]