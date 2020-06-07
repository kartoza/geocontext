PROJECT_ID := geocontext
PROD_SERVER := geocontext.kartoza.com
SHELL := /bin/bash

default: web
setup-web: build permissions web pause migrate collectstatic

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) build uwsgi

permissions:
	@if [ ! -d "logs" ]; then mkdir logs; fi
	@if [ ! -d "media" ]; then mkdir media; fi
	@if [ ! -d "static" ]; then mkdir static; fi
	@if [ ! -d "backups" ]; then mkdir backups; fi
	@if [ -d "logs" ]; then sudo chmod -R a+rwx logs; fi
	@if [ -d "media" ]; then sudo chmod -R a+rwx media; fi
	@if [ -d "static" ]; then sudo chmod -R a+rwx static; fi
	@if [ -d "pg" ]; then sudo chmod -R a+rwx pg; fi
	@if [ -d "backups" ]; then sudo chmod -R a+rwx backups; fi

web:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up -d web
	@# Dont confuse this with the dbbackup make command below
	@# This one runs the postgis-backup cron container
	@# We add --no-recreate so that it does not destroy & recreate the db container
	@docker-compose -p $(PROJECT_ID) up --no-recreate --no-deps -d dbbackups

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
	@./production/push-production.sh

# ----------------------------------------------------------------------------
#  Development
# ----------------------------------------------------------------------------

setup-dev: setup-web superuser import-data build-devweb devweb
run-dev: web devweb

devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in DEVELOPMENT mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up --no-deps -d devweb

build-devweb: db
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building devweb"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) build devweb

# ----------------------------------------------------------------------------
# Django administration
# ----------------------------------------------------------------------------

shell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi /bin/bash

pyshell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running Python Django interpreter"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py shell

superuser:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Creating a superuser in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py createsuperuser

migrate:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running migrate in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py migrate

makemigrations:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running update migrations in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py makemigrations

collectstatic:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Collecting static in production mode"
	@echo "------------------------------------------------------------------"
	@docker exec $(PROJECT_ID)-uwsgi python manage.py collectstatic --noinput

import-web-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec dev-web python manage.py import_data $(FILE_URI)

export-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Exporting GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py export_data

import-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py import_data $(FILE_URI)

delete-data:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Importing GeoContext Data."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py delete_data

delete-cache:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Delete cache."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) exec uwsgi python manage.py delete_cache

flake8:
	@echo "Check flake 8"
	@flake8 ../django_project

test:
	@docker-compose -p $(PROJECT_ID) exec devweb python -W ignore manage.py test

# ----------------------------------------------------------------------------
# Server Administration
# ----------------------------------------------------------------------------

reload:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Reload django project in production mode"
	@echo "------------------------------------------------------------------"
	@docker exec $(PROJECT_ID)-uwsgi uwsgi --reload  /tmp/django.pid

logs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing uwsgi logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) logs uwsgi

nginx:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running nginx in production mode"
	@echo "Normally you should use this only for testing"
	@echo "In a production environment you will typically use nginx running"
	@echo "on the host rather if you have a multi-site host."
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up -d nginx
	@echo "Site should now be available at http://localhost"

# ----------------------------------------------------------------------------
# Docker administration
# ----------------------------------------------------------------------------

rm: dbbackup rm-only

kill:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Killing in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) kill

rm-only: kill
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing production instance!!! "
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) rm

status:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Show status for all containers"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) ps

# ----------------------------------------------------------------------------
# Database administration
# ----------------------------------------------------------------------------

db:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running db in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) up -d db

dblogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing db logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) logs db

nginxlogs:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Showing nginx logs in production mode"
	@echo "------------------------------------------------------------------"
	@docker-compose -p $(PROJECT_ID) logs web

dbbash:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Bashing in to production database"
	@echo "------------------------------------------------------------------"
	@docker exec -t -i $(PROJECT_ID)-db /bin/bash

dbsnapshot:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Grab a quick snapshot of the database and place in the host filesystem"
	@echo "------------------------------------------------------------------"
	@docker exec -t -i $(PROJECT_ID)-db /bin/bash -c "PGPASSWORD=docker pg_dump -Fc -h localhost -U docker -f /tmp/$(PROJECT_ID)-snapshot.dmp gis"
	@docker cp $(PROJECT_ID)-db:/tmp/$(PROJECT_ID)-snapshot.dmp .
	@docker exec -t -i $(PROJECT_ID)-db /bin/bash -c "rm /tmp/$(PROJECT_ID)-snapshot.dmp"
	@ls -lahtr *.dmp

dbschema:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Print the database schema to stdio"
	@echo "------------------------------------------------------------------"
	@docker exec -t -i $(PROJECT_ID)-db /bin/bash -c "PGPASSWORD=docker pg_dump -s -h localhost -U docker gis"

dbshell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in in production database"
	@echo "------------------------------------------------------------------"
	@docker exec -t -i $(PROJECT_ID)-db psql -U docker -h localhost gis

dbrestore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp in production mode"
	@echo "------------------------------------------------------------------"
	@# - prefix causes command to continue even if it fails
	-@docker exec -t -i $(PROJECT_ID)-db su - postgres -c "dropdb gis"
	@docker exec -t -i $(PROJECT_ID)-db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker exec -t -i $(PROJECT_ID)-db pg_restore /backups/latest.dmp | docker exec -i $(PROJECT_ID)-db su - postgres -c "psql gis"

db-fresh-restore:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Restore dump from backups/latest.dmp in production mode"
	@echo "------------------------------------------------------------------"
	-@docker exec -t -i $(PROJECT_ID)-db su - postgres -c "dropdb gis"
	@docker exec -t -i $(PROJECT_ID)-db su - postgres -c "createdb -O docker -T template_postgis gis"
	@docker exec -t -i $(PROJECT_ID)-db su - postgres -c "psql gis -f /sql/migration.sql"

dbbackup:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Create `date +%d-%B-%Y`.dmp in production mode"
	@echo "Warning: backups/latest.dmp will be replaced with a symlink to the new backup."
	@echo "------------------------------------------------------------------"
	@# - prefix causes command to continue even if it fails
	@# Explicitly don't use -it so we can call this make target over a remote ssh session
	@docker exec $(PROJECT_ID)-db-backups /backups.sh
	@docker exec $(PROJECT_ID)-db-backups cat /var/log/cron.log | tail -2 | head -1 | awk '{print $4}'
	@if [ -f "backups/latest.dmp" ]; then rm backups/latest.dmp; fi
	# backups is intentionally missing from front of first clause below otherwise symlink comes out with wrong path...
	-@ln -s `date +%Y`/`date +%B`/PG_$(PROJECT_ID)_gis.`date +%d-%B-%Y`.dmp backups/latest.dmp
	@echo "Backup should be at: backups/`date +%Y`/`date +%B`/PG_$(PROJECT_ID)_gis.`date +%d-%B-%Y`.dmp"

# ----------------------------------------------------------------------------
help:
	@echo "-------------------------------GEOCONTEXT--------------------------------------"
	@echo ""
	@echo "---------------------------------SETUP-----------------------------------------"
	@echo ""
	@echo "setup-dev        :Dev shortcut - builds web + dev containers, configure & load data."
	@echo "run-dev          :Start up dev container"
	@echo "setup-web        :Builds, configures and runs the production containers"
	@echo "web              :Default - runs the production site."
	@echo "deploy           :Extends uwsgi image with production, tag and push."
	@echo ""
	@echo ""
	@echo "-----------------------------Django Administration-----------------------------"
	@echo ""
	@echo "shell            :Open a bash shell in the uwsgi container."
	@echo "pyshell          :Open a Python Django session in the uwsgi container."
	@echo "superuser        :Create a django superuser account."
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
	@echo "rm               :Remove all containers."
	@echo "rm-only          :Remove any containers without trying to kill them first. "
	@echo "logs             :View the logs of all running containers. Note that you can also view individual logs in the deployment/logs directory."
	@echo "permissions      :Update the permissions of shared volumes. Note this will destroy any existing permissions you have in place."
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