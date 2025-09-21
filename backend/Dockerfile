FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev git --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /app/
RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction
COPY app /app/app
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
