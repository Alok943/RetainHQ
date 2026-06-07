FROM python:3.11-slim

WORKDIR /app

# Copy application code FIRST so hatchling can find the 'app' module during pip install
COPY . .

# Install dependencies and the application package
RUN pip install --no-cache-dir .

# Railway sets PORT dynamically. Run migrations before starting the server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
