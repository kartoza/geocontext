# GeoContext

A django project to retrieve information of a point.

View a running instance at [http://geocontext.kartoza.com](http://geocontext.kartoza.com)

The latest source code is available at
[https://github.com/kartoza/geocontext](https://github.com/kartoza/geocontext).

## Project activity

* Current test status master: [![Build Status](https://travis-ci.org/kartoza/geocontext.svg?branch=master)](https://travis-ci.org/kartoza/geocontext) and
[![Code Health](https://landscape.io/github/kartoza/geocontext/master/landscape.svg?style=flat)](https://landscape.io/github/kartoza/geocontext/master)

* Current test status develop: [![Build Status](https://travis-ci.org/kartoza/geocontext.svg?branch=develop)](https://travis-ci.org/kartoza/geocontext) and
[![Code Health](https://landscape.io/github/kartoza/geocontext/develop/landscape.svg?style=flat)](https://landscape.io/github/kartoza/geocontext/develop)

## Key features

* Stateless and easy to deploy
* Able to retrieve geo-context information of a point from several services
* Optimized for rapid information retrieval
* Currently supports WFS, WMS, ArcREST and Placename sources
* Using cache mechanism to retrieve context frequently requested information
* Three level hierarchy (service --> group --> collection) to sort services to request
* Simple API returning json data


## API
After you have working geocontext instance, you can then check the available 
API from the API documentation links (you can find it in the main page) or 
see the content and the hierarchy of context service (you can also 
find the link in the main page)

### v2
New endpoints accepting url key:val parameters.
* `/api/v2/service?`
* `/api/v2/group?`
* `/api/v2/collection?`

*Required parameters:*
* `x` - Longitude in DD, DM, or DMS
* `y` - Latitude in DD, DM, or DMS
* `Key` - Key of service/grou/collection to query

*Optional parameters:*
* `srid` - Query EPSG Coordinate reference system code (default: Pseudo-mercator 4326)
* `tolerance` - Search distance around query point in meters (default: specified per service)

## Quick Installation Guide

For deployment we use [docker](http://docker.com) so you need to have docker
running on the host. GeoContext is a django app so it will help if you have
some knowledge of running a django site.

1. Clone the project
```bash
git clone git://github.com/kartoza/geocontext.git
```
2. Ensure shared volume permissions are set
```bash
make permissions
```
3. Setup and run the web service: available on `http://localhost/`
```bash
make setup-web
```
4. If needed, create a superuser for Django admin access on `http://localhost/admin/` - here you can manually modify data
```bash
make superuser
```

**Loading Data**
GeoContext use a json file to populate the context service and its 
group and collection. Everything is stored in [geocontext.json](https://github.com/kartoza/geocontext/blob/develop/django_project/base/management/commands/geocontext.json).
You can load it by running this command:
```bash
make import-data
``` 
Or if you have your own json file, you can load it with:
```bash
make import-data FILE_URI=path/to/your/json/file
```
Be careful, it will replace your context service data (and its 
hierarchy) with your new one from the json file. But no worries, when your 
run this `import-data` command, it will export your context service 
data to a new json file.

You can also export your context service to json file by running:
```bash
make export-data
```

## Developers quick start with Docker and VSCode

An easy way to set up a locally development environment is with Docker and VSCode.

1. Optional: add any ENV variables needed to for uwsgi & dvweb to `/deployment/.env`
2. Use setup-dev to build the production and development containers, create superuser,
and import default services.
```bash
make setup-dev
```
3. Geocontext should now be running at localhost.
4. DB can be accessed at port 'localhost:25432', user&password='docker', database=gis
5. Attach a VSCode session by right clicking on the running geocontext_devweb container in the [VSCode remote - Containers](https://code.visualstudio.com/docs/remote/containers) extension
6. Now we can get into the running containers to run management commands, run another server at another port, debug etc.
7. In the geocontext_devweb container terminal you can run a test server for debugging as follows:
```
python manage.py runserver 8001
```
7. Flake8 linting can be run with:
```bash
make flake8
```
8. Pytest is used for testing and and can be run with:
```bash
make test
```
9. See README-legacy for PyCharm and SSH access to devweb container.

## Deployment

1. Config git repo/branch and dockerhub/image:tag to use for deploy in top of Makefile
2. Run make command to build and push image
```
make deploy
```
* Note the UWSGI image must be available (setup-dev / setup-web)


## Participation

We work under the philosophy that stakeholders should have access to the
development and source code, and be able to participate in every level of the
project - we invite comments, suggestions and contributions.  See
[our milestones list](https://github.com/kartoza/geocontext/milestones) and
[our open issues list](https://github.com/kartoza/geocontext/issues?page=1&state=open)
for known bugs and outstanding tasks. 

## Credits

GeoContext was funded by [JRS](http://jrsbiodiversity.org/) and developed by [Kartoza.com](http://kartoza.com), [Freshwater Research Center](http://frcsa.org.za) and individual contributors.

## License

GeoContext is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License version 3 (GPLv3) as
published by the Free Software Foundation.

The full GNU General Public License is available in LICENSE.txt or
http://www.gnu.org/licenses/gpl.html


## Disclaimer of Warranty (GPLv3)

There is no warranty for the program, to the extent permitted by
applicable law. Except when otherwise stated in writing the copyright
holders and/or other parties provide the program "as is" without warranty
of any kind, either expressed or implied, including, but not limited to,
the implied warranties of merchantability and fitness for a particular
purpose. The entire risk as to the quality and performance of the program
is with you. Should the program prove defective, you assume the cost of
all necessary servicing, repair or correction.

## Thank you

Thank you to the individual contributors who have helped to build GeoContext:

* Tim Sutton ([@timlinux](https://github.com/timlinux)) : tim@kartoza.com
* Ismail Sunni (@ismailsunni)
* Dimas Tri Ciputra ([@dimasciput](https://github.com/dimasciput)) : 
dimas@kartoza.com
* Andre Theron ([@andretheronsa](https://github.com/andretheronsa)) : 
andre.theron@kartoza.com
