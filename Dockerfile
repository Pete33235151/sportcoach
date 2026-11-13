FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
COPY frontend ./frontend
RUN pip install --no-cache-dir .
ENV SPORTCOACH_DATABASE_URL=sqlite:////data/sportcoach.sqlite3
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
