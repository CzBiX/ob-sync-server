FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

VOLUME [ "/app/data" ]
EXPOSE 8000

COPY ./src src

CMD [ "uvicorn", "--host", "0.0.0.0", "--port", "8000", "src.web:app" ]