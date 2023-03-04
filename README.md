# DJANGO TELEGRAM BOT TEMPLATE

## Dependencies

    pyenv install 3.10.0 &&
    pyenv local 3.10.0 &&
    python -m pip install poetry &&
    python -m poetry install &&
    poetry run pre-commit install

## ENV setup

__*rename .env-template/, .env-template/.dev.env-template, .env-template/.prod.env-template to .env/, .env/.dev.env, .env/.prod.env*__

## First run

1. Build the new image and spin up the two containers
    ```docker-compose up -d --build```

2. Run the migrations
    ```docker-compose exec web python manage.py migrate --noinput```

3. Create default django database tables
   ```docker-compose exec db psql --username=django_tg_bot --dbname=django_tg_bot_dev```
   *rename __django_tg_bot__ to your database table name setted in __.env__ settings*

4. Define your bot token __TELEGRAM_BOT_TOKEN__ in .env files

### Development

    make dev-up
    make dev-down

### Production

    make prod-up
    make prod-down

#### Unordered

* Rewrite bot to webhook
* Add traefik ssl production
