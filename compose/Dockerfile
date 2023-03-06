FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc python3-dev musl-dev build-essential gettext procps \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir --upgrade poetry==1.3.1

COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.in-project false

WORKDIR /app

RUN poetry install --no-dev

COPY ./compose/entrypoint.sh /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

COPY ./compose/django/start-django.sh /start-django
RUN sed -i 's/\r$//g' /start-django && chmod +x /start-django

COPY ./compose/django/celery/start-worker.sh /start-worker
RUN sed -i 's/\r$//g' /start-worker && chmod +x /start-worker

COPY ./compose/django/celery/start-beat.sh /start-beat
RUN sed -i 's/\r$//g' /start-beat && chmod +x /start-beat

COPY ./compose/django/celery/start-flower.sh /start-flower
RUN sed -i 's/\r$//g' /start-flower && chmod +x /start-flower

COPY ./compose/django/start-bot.sh /start-bot
RUN sed -i 's/\r$//g' /start-bot && chmod +x /start-bot

ENTRYPOINT ["/entrypoint"]
