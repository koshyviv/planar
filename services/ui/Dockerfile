FROM python:3.12-slim
WORKDIR /app
COPY services/ui/index.html /app/index.html
CMD ["python3", "-m", "http.server", "3000", "--directory", "/app"]
