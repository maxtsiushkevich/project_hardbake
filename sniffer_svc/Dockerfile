FROM python:3.12

EXPOSE 8000

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY api/ ./api/

CMD ["python", "-m", "api.main"]
