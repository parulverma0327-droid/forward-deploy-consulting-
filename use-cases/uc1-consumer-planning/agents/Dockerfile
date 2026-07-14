FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt flask>=3.0.0

COPY forecast_signal/ ./forecast_signal/
COPY orchestrator/ ./orchestrator/
COPY demand_sensing/ ./demand_sensing/

ENV PORT=8080
CMD ["python", "orchestrator/main.py"]
