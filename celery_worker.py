import os
from celery import Celery
from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))
celery = Celery(app.import_name)
celery.conf.update(app.config)

@celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

if __name__ == '__main__':
    celery.start()
