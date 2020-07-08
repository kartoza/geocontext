# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [TO DO]

### Add
- Map view with global basemap and collections on main page
- Sentry
- Test value + coordinates for all services. Activate cron

### Deprecate
- CoreAPI in favour of OpenAPI new standards (swagger etc...)

### Fix
- Ensure we get geometries from requests. WFS does not reliably return geometries currently
- Backups not active


## [2.0.0] - 2020-07-01
### Added
- Async external requests for speed.
- Query point saved to Cache if no geometry returned - multiple requests within `tolerance` of query points will hit the cache instead of external requests.
- We only return the closest feature with the query tolerance found in cache - and if multiple geometries are returned from external requests we only use the closest one.
- Added a Query model and related utilities to allow us to log all query locations, types and times.
- Service model has new fields: `create_time`, `tolerance`, `test_x`, `test_y`, `test_val` and `status`. 
- The Service model test fields can be used to load known responses to allow for automated test of the service status.
- Cache model has new field: `create_time`
- api v2 views - endpoints for `service`, `group` and `collection`. We can now directly query a service.
- api v2 endpoints accept url get requests with keyword parameters: `x`, `y`, `key` and optional `srid` and `tolerance`.
- Queries in SRIDs different than `EPSG:4326` is possible.
- Query coordinate format now allows for DMS, DM, and DD (signed or with added direction)
- Parse esri geometry types to GEOS from ArcREST services.
- Pytest 
- Coverage
- Cron jobs to clear expired cache values and check service status

### Changed
- `result_regex` service model attribute split into `layer_namespace` & `layer_name`. `layer_name` is the base feature name and used for service with a more simple request format than geoserver (such as placename)
- `layer_typename` service model attribute split into `layer_workspace` & `layer_typename`
- `service_registry_values` in response now `service_values`
- External request and cache query and update logic split from model instance. The cache is now queried first, services not found in cache collected and sent for async fetching, new values is then added to cache. Async http requests provide a major speed boost but the ORM is a blocker to the event loop.
- Minimal round trips done for external requests - we no longer do a WFS `getCapabilities` request - just query straight. We no longer ask for the geometry type before attempting a WFS intersect filter - we try the filter and if no response then we fall back to BBOX query. This means polygon intersects only require single requests.
- All requests now ask for JSON data - simplifies parsing.
- Geometries collected from services now flattened to 2d.
- Complex geometries may take long to parse and block the eventloop - we attempt to spin these large file CPU bound processes off from the main loop using a threadpool.
- Cache geometry field now pinned to Pseudomercator 3857 - to simplify and speed up distance queries. Accurate long range measurements is not required.
- Query cache now properly based on expiry time and distance from query point (using new `tolerance`)
- Renaming accros the project to simplify and imporve readability.
    * All redundant use of the word `context` is removed. `context_group` is now simply `group`.
    * `context_service_registry` is now simply `service`.
- Restructuring of project - logic now fits more neatly into `models`/`serializers`/`utilities`/`views` sorted into `service`/`group`/`collection`.
- Makefile now simplified with simple commands to setup either a dev or web local instance.
- Simplified deployment structure to only one requirement.txt (there was 3)
- Optimized docker build to use fewer layers and smaller base images.

### Deprecated 
- 'graphable' property of groups - the use case of this as a high level attribute is not
clear. It is not expected that users will blindly be looking for data to graph and whether a dataset
is graphable or not should therefore be up to the discretion of the user.
- OWSlib for WMS requests - very slow initialize method
- TravisCI in favour of Github actions

### Upgraded 
- Debian stretch to Buster
- Python 3.6 to 3.8
- Django 1.8 to 3.0
- PostGis 2 to 3
- Postgresql 9 to 12
- requests to aioHTTP[speedups]

### Removed
- Multiple geometry fields in cache model - in favour of a single geometry field
- Automated tests that relied on external service requests.
- Removed various references, unused modules, packages and folders related to legacy Geocontext and it's parent project.

### Fixed
- Change bounding box formula which was simply a fraction of coordinate. This resulted in results that may not be reproducible. The new bounding box is calculated based on disttance in the correct projection and is guaranteed to include features within `tolerance` specified by query or service.
- Geometries should now be added to cache if return by server.
- Services on main page now listed in Alphabetical order

### Security
- Various security improvements related to upgraded dependencies
- Packages in requests now pinned to minor versions but allow patch (X.y.*)