FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 wepulse && mkdir -p /app/data && chown -R wepulse:wepulse /app
USER wepulse

EXPOSE 8765
CMD ["python", "-m", "wepulse"]
