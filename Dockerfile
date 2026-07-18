FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY orchestrator /app/orchestrator
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini
COPY docs /app/docs
COPY examples /app/examples
COPY generated_projects /app/generated_projects

EXPOSE 8000

CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
