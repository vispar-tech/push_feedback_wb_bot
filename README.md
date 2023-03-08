# WildBerries PushFeedback BOT 🔔

## Dependencies

    pyenv install 3.10.0 && pyenv local 3.10.0 && python -m pip install poetry && python -m poetry install && poetry run pre-commit install

## ENV setup

__*rename .env-template/, .env-template/.dev.env-template, .env-template/.prod.env-template to .env/, .env/.dev.env, .env/.prod.env*__

## First run

1. Build the new image and spin up the two containers
    ```make dev-up```

2. Run the migrations
    ```docker-compose exec web python manage.py migrate --noinput```

3. Create default django database tables
   ```docker-compose exec db psql --username=push_feedback_wb --dbname=push_feedback_wb_dev```
   *rename __push_feedback_wb__ to your database table name setted in __.env__ settings*

4. Define your bot token __TELEGRAM_BOT_TOKEN__ in .env files

5. Define your spreadsheet_id __SPREADSHEET_ID__ in .env files

### Development

    make dev-up
    make dev-down
    make dev-restart

### Production

    make prod-up
    make prod-down
    make prod-restart
