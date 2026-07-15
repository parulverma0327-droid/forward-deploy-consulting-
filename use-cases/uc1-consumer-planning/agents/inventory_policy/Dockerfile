FROM python:3.11-slim

WORKDIR /app

COPY requirements-cloudrun.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./inventory_policy/

ENV PORT=8080
CMD ["python", "inventory_policy/main.py"]
