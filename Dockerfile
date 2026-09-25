FROM python:3.11-slim
WORKDIR /app
ENV ENERGY_PROJECT_ROOT=/app
COPY pyproject.toml README.md ./
COPY src ./src
COPY dashboard ./dashboard
COPY dbt ./dbt
RUN pip install --no-cache-dir .
EXPOSE 8501
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0"]
