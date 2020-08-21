PROD_SERVER := geocontext.kartoza.com
PROJECT_ID := geocontext
SHELL := /bin/bash

# DEPLOY CONFIG HERE
export GIT := andretheronsa  # Default kartoza
export REPO := geocontext  # Default geocontext
export BRANCH := 2.0  # Default master
export DOCKER := andretheronsa  # Default andretheronsa
export IMAGE := geocontext  # Default geocontext
export TAG := 2.0  # Default latest

default: start-web
setup-web: build start-web pause migrate collectstatic

generate-k8s-manifests:
	@kompose convert --out k8s

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building uwsgi"
	@echo "------------------------------------------------------------------"
	@docker-compose build uwsgi

permissions:
	@if [ ! -d "logs" ]; then mkdir logs; fi
	@if [ ! -d "media" ]; then mkdir media; fi
	@if [ ! -d "static" ]; then mkdir static; fi
	@if [ ! -d "backups" ]; then mkdir backups; fi
	@mkdir -p reports
	@mkdir -p sql
	@if [ -d "logs" ]; then sudo chmod -R a+rwx logs; fi
	@if [ -d "media" ]; then sudo chmod -R a+rwx media; fi
	@if [ -d "static" ]; then sudo chmod -R a+rwx static; fi
	@if [ -d "pg" ]; then sudo chmod -R a+rwx pg; fi
	@if [ -d "backups" ]; then sudo chmod -R a+rwx backups; fi
	@sudo chmod -R a+rwx reports sql

uwsgi:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Spin up UWSGI container"
	@echo "------------------------------------------------------------------"
	@docker-compose up -d uwsgi

start-web:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Spin up NGINX web and DB backups"
	@echo "------------------------------------------------------------------"
	@docker-compose up -d web
	@# Dont confuse this with the dbbackup make command below
	@# This one runs the postgis-backup cron container
	@# We add --no-recreate so that it does not destroy & recreate the db container
	@docker-compose up --no-recreate --no-deps -d dbbackups

pause:
	@echo "Allow 10s for db to start up"
	@sleep 10

# ----------------------------------------------------------------------------
# Production 
# ----------------------------------------------------------------------------
deploy:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Pushing image to production"
	@echo "------------------------------------------------------------------"
	@production/push-production.sh

# ----------------------------------------------------------------------------
#  Development
# ----------------------------------------------------------------------------

setup-dev: build uwsgi pause migrate collectstatic import-data build-devweb devweb
start-dev: devweb

devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in DEVELOPMENT mode"
	@echo "------------------------------------------------------------------"
	@docker-compose up --no-deps -d devweb

build-devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building devweb"
	@echo "------------------------------------------------------------------"
	@docker-compose build devweb

# ----------------------------------------------------------------------------
# Django administration
# ----------------------------------------------------------------------------

shell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in uwsgi"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi /bin/bash

pyshell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running Python Django interpreter"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py shell

superuser:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Creating a superuser"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py createsuperuser

migrate:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running migrate"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py migrate

makemigrations:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running update migrations"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py makemigrations

collectstatic:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Collecting static"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py collectstatic --noinput

import-web-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose exec dev-web python manage.py import_data $(FILE_URI)

export-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Exporting GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py export_data

import-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py import_data $(FILE_URI)

delete-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py delete_data

delete-cache:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Delete cache."
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi python manage.py delete_cache

test-full:
	@docker-compose exec devweb pytest \
		--cov=geocontext geocontext/tests/  \
		--doctest-modules \
		--ignore-glob="*aiohttp/helpers.py" \
		--ignore-glob="*__init__.py" \
		--flake8

test:
	@docker-compose exec devweb pytest

test-coverage:
	@docker-compose exec devweb pytest --cov=geocontext geocontext/tests/

test-docs:
	@docker-compose exec devweb pytest --doctest-modules

test-flake8:
	@docker-compose exec devweb pytest --flake8

# ----------------------------------------------------------------------------
# Server Administration
# ----------------------------------------------------------------------------

reload:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Reload Django"
	@echo "------------------------------------------------------------------"
	@docker-compose exec uwsgi uwsgi --reload  /tmp/django.pid

logs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing uwsgi logs"
	@echo "------------------------------------------------------------------"
	@docker-compose logs uwsgi

nginx:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running nginx"
	@echo "------------------------------------------------------------------"
	@docker-compose up -d nginx
	@echo "Site should now be available at http://localhost"

# ----------------------------------------------------------------------------
# Docker administration
# ----------------------------------------------------------------------------

rm: dbbackup rm-only

stop:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Stoppping and removing containers"
	@echo "------------------------------------------------------------------"
	@docker-compose down

kill:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Killing all containers"
	@echo "------------------------------------------------------------------"
	@docker-compose kill

rm-only: kill
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Killing and removing all containers"
	@echo "------------------------------------------------------------------"
	@docker-compose rm

status:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Show status for all containers"
	@echo "------------------------------------------------------------------"
	@docker-compose ps

# ----------------------------------------------------------------------------
# Database administration
# ----------------------------------------------------------------------------

db:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running db"
	@echo "------------------------------------------------------------------"
	@docker-compose up -d db

dblogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing db logs"
	@echo "------------------------------------------------------------------"
	@docker-compose logs db

nginxlogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing nginx logs"
	@echo "------------------------------------------------------------------"
	@docker-compose logs web

dbbash:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Bashing in to production database"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash

dbsnapshot:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Grab a quick snapshot of the database and place in the host filesystem"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash -c "PGPASSWORD=docker pg_dump -Fc -h localhost -U docker -f /tmp/$(PROJECT_ID)-snapshot.dmp gis"
	@docker cp $(PROJECT_ID)_db_1:/tmp/$(PROJECT_ID)-snapshot.dmp .
	@docker-compose exec db /bin/bash -c "rm /tmp/$(PROJECT_ID)-snapshot.dmp"
	@ls -lahtr *.dmp

dbschema:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Print the database schema to stdio"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db /bin/bash -c "PGPASSWORD=docker pg_dump -s -h localhost -U docker gis"

dbshell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in in production database"
	@echo "------------------------------------------------------------------"
	@docker-compose exec db psql -U docker -h localhost gis

dbrestore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp"
	@echo "------------------------------------------------------------------"
	@# - prefix causes command to continue even if it fails
	-@docker-compose exec db su - postgres -c "dropdb gis"
	@docker-compose exec db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker-compose exec db pg_restore backups/latest.dmp | docker-compose exec -i db su - postgres -c "psql gis"

db-fresh-restore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp"
	@echo "------------------------------------------------------------------"
	-@docker-compose exec db su - postgres -c "dropdb gis"
	@docker-compose exec db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker-compose exec db su - postgres -c "psql gis -f /sql/migration.sql"

dbbackup:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Create `date +%d-%B-%Y`.dmp"
	@echo "Warning: backups/latest.dmp will be replaced with a symlink to the new backup."
	@echo "------------------------------------------------------------------"
	@docker-compose exec dbbackups /backups.sh
	@docker-compose exec dbbackups cat /var/log/cron.log | tail -2 | head -1 | awk '{print $4}'
	-@if [ -f "backups/latest.dmp" ]; then rm backups/latest.dmp; fi
	-@ln -s `date +%Y`/`date +%B`/PG_$(PROJECT_ID)_gis.`date +%d-%B-%Y`.dmp backups/latest.dmp
	@echo "Backup should be at: /deployment/backups/`date +%Y`/`date +%B`/PG_$(PROJECT_ID)_gis.`date +%d-%B-%Y`.dmp"

# ----------------------------------------------------------------------------
help:
	@echo "-------------------------------GEOCONTEXT--------------------------------------"
	@echo ""
	@echo "---------------------------------General---------------------------------------"
	@echo ""
	@echo "permissions      :Update the permissions of shared volumes. Note this will destroy any existing permissions you have in place."
	@echo "setup-dev        :Dev shortcut - builds uwsgi + dev containers, configure & load data."
	@echo "start-dev        :Start up dev container"
	@echo "setup-web        :Builds, configures and runs the production containers inlcuding web server. Does not load data."
	@echo "start-web        :Default - runs the web server."
	@echo "import-data      :Import geojson service data"
	@echo "stop             :Stop and remove running containers."
	@echo "deploy           :Extends uwsgi image with production, tag and push. Config in Makefile. Default=kartoza/geocontext:master."
	@echo ""
	@echo ""
	@echo "-----------------------------Django Administration-----------------------------"
	@echo ""
	@echo "superuser        :Create a django superuser account."
	@echo "shell            :Open a bash shell in the uwsgi container."
	@echo "pyshell          :Open a Python Django session in the uwsgi container."
	@echo "test             :Run tests on development."
	@echo "flake8           :Check flake8."
	@echo "collectstatic    :Run the django collectstatic command."
	@echo "makemigrations   :Freshen all migration definitions to match the current code base."
	@echo "migrate          :Run any pending migrations. "
	@echo ""
	@echo "-----------------------------Docker Administration-----------------------------"
	@echo ""
	@echo "reload           :Reload the uwsgi process. Useful when you need django to pick up any changes you may have deployed."
	@echo "build            :Builds all required containers."
	@echo "build-devweb     :Build the development container. See [development notes](README-dev.md)."
	@echo "devweb           :Create an ssh container derived from uwsgi that can be used as a remote interpreter for PyCharm. See [development notes](README-dev.md)."
	@echo "rm               :Make a db backup and remove all containers."
	@echo "rm-only          :Kills and removes all containers."
	@echo "logs             :View the logs of all running containers. Note that you can also view individual logs in the deployment/logs directory."
	@echo "kill             :Kills all running containers. Does not remove them."
	@echo ""
	@echo "-----------------------------Server Administration-----------------------------"
	@echo ""
	@echo "nginx            :Builds and runs the nginx container."
	@echo "logs             :View the uwsgi activity logs."
	@echo "nginxlogs        :View the nginx activity logs."
	@echo ""
	@echo "-----------------------------Database------------------------------------------"
	@echo ""
	@echo "db               :Build and run the db container."
	@echo "dbbackup         :Make a snapshot of the database, saving it to deployments/backups/YYYY/MM/project-DDMMYYYY.dmp. It also creates a symlink to backups/latest.dmp for the latest backup."
	@echo "dbbash           :Open a bash shell inside the database container."
	@echo "dblogs           :View the database logs."
	@echo "dbrestore        :Restore deployment/backups/latest.dmp over the active database. Will delete any existing data in your database and replace with the restore, so **use with caution**."
	@echo "dbschema         :Dump the current db schema (without data) to stdio. Useful if you want to compare changes between instances."
	@echo "dbshell          :Get a psql prompt into the db container. "
	@echo "dbsnapshot       :As above but makes the backup as deployment/snapshot.smp - replacing any pre-existing snapshot."
