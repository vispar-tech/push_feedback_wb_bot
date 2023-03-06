.PHONY: dev-up dev-down prod-up prod-down migrate collectstatic

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

dev-up:
	docker compose up -d --build

dev-down:
	docker compose down

migrate:
	poetry run python ./src/manage.py makemigrations --noinput
	poetry run python ./src/manage.py migrate --noinput

collectstatic:
	poetry run python ./src/manage.py collectstatic --noinput
