release: flask db upgrade
web: gunicorn "app:create_app()" --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
worker: celery -A celery_worker worker --loglevel=info
