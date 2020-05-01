# GeoContext

A django project to retrieve information of a point.

View a running instance at [http://geocontext.kartoza.com](http://geocontext.kartoza.com)

The latest source code is available at
[https://github.com/kartoza/geocontext](https://github.com/kartoza/geocontext).

* **Developers:** See our [developer guide](README-dev.md)
* **For production:** See our [deployment guide](README-docker.md)


## Key features

* Stateless and easy to deploy
* Able to retrieve context information of a point from several sources 
(context service registries)
* Currently work with WFS and WMS sources
* Using cache mechanism to retrieve context information faster
* Two level hierarchy (context service registry --> context group --> context
 collection) for easier to manage
* Simple API


## Project activity

* Current test status master: [![Build Status](https://travis-ci.org/kartoza/geocontext.svg?branch=master)](https://travis-ci.org/kartoza/geocontext) and
[![Code Health](https://landscape.io/github/kartoza/geocontext/master/landscape.svg?style=flat)](https://landscape.io/github/kartoza/geocontext/master)

* Current test status develop: [![Build Status](https://travis-ci.org/kartoza/geocontext.svg?branch=develop)](https://travis-ci.org/kartoza/geocontext) and
[![Code Health](https://landscape.io/github/kartoza/geocontext/develop/landscape.svg?style=flat)](https://landscape.io/github/kartoza/geocontext/develop)




## Quick Installation Guide

For deployment we use [docker](http://docker.com) so you need to have docker
running on the host. GeoContext is a django app so it will help if you have
some knowledge of running a django site.

```
git clone git://github.com/kartoza/geocontext.git
cd geocontext/deployment
cp btsync-db.env.EXAMPLE btsync-db.env
cp btsync-media.env.EXAMPLE btsync-media.env
make build
make permissions
make web
# Wait a few seconds for the DB to start before to do the next command
make migrate
make collectstatic
```


So as to create your admin account:
```
make superuser
```

**Loading Data**
GeoContext use a json file to populate the context service registry and its 
group and collection. Everything is stored in [geocontext.json](https://github.com/kartoza/geocontext/blob/develop/django_project/base/management/commands/geocontext.json).
You can load it by running this command:
```bash
make import-data
``` 
Or if you have your own json file, you can load it with:
```bash
make import-data FILE_URI=path/to/your/json/file
```
Be careful, it will replace your context service registry data (and its 
hierarchy) with your new one from the json file. But no worries, when your 
run this `import-data` command, it will export your context service registry 
data to a new json file.

You can also export your context service registry to json file by running:
```bash
make export-data
```

## API
After you have working geocontext instance, you can then check the available 
API from the API documentation links (you can find it in the main page) or 
see the content and the hierarchy of context service registry (you can also 
find the link in the main page)


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
* Andre Theron ([@andretheronsa](https://github.com/andretheronsa)) : 
andre.theron@kartoza.com
* Dimas Tri Ciputra ([@dimasciput](https://github.com/dimasciput)) : 
dimas@kartoza.com
