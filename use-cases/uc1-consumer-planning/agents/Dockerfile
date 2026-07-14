FROM python:3.11-slim

WORKDIR /app

COPY requirements-cloudrun.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY forecast_signal/ ./forecast_signal/
COPY orchestrator/ ./orchestrator/

ENV PORT=8080
CMD ["python", "orchestrator/main.py"]
