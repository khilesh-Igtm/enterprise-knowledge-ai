
from celery import Celery
from celery.signals import worker_ready

from app.core.config import settings

REDIS_URL = settings.REDIS_URL

celery_app = Celery(
    "enterprise_knowledge_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.worker.tasks.document_tasks",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Execution
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Reliability
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 3600,
    },

    # Results
    result_expires=3600,

    # Time
    timezone="UTC",
    enable_utc=True,

    # Avoid accidental duplicate execution
    task_ignore_result=False,
)


@worker_ready.connect
def on_worker_ready(**kwargs):
    print("Enterprise Knowledge AI worker is ready.")