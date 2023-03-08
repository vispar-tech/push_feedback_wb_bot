.PHONY: dev-up dev-down prod-up prod-down migrate collectstatic

prod-restart:
	docker compose -f docker-compose.prod.yml down
	docker compose -f docker-compose.prod.yml up -d --build

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

dev-restart:
	docker compose down
	docker compose up -d --build

dev-up:
	docker compose up -d --build

dev-down:
	docker compose down

migrate:
	poetry run python ./src/manage.py makemigrations --noinput
	poetry run python ./src/manage.py migrate --noinput

collectstatic:
	poetry run python ./src/manage.py collectstatic --noinput
