FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN adduser --disabled-password --gecos "" appuser

RUN mkdir -p /app/images
RUN chown -R appuser:appuser /app/images 
RUN chmod 755 /app/images

COPY . .
USER appuser
EXPOSE 5002

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "app:app"]
