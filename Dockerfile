FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY csc /app/csc
COPY configs /app/configs
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "csc.service", "--host", "0.0.0.0", "--port", "8080"]
