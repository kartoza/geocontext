# How to do local deployment

Local deployment are configured by overriding default production mode.

Copy the `sample.env` file as `.env` and change the values inside as necessary.

Copy `docker-compose.override.sample.yml` as `docker-compose.override.yml` and 
change the values inside as necessary.

Production deployment needs to specify persistence as volumes declaration. 
This helps translates deployment to production.

Local deployment may bind mount the volume to host (as seen in the volumes 
declaration in docker-compose.override.yml) or, bind mount the host path 
directly in the container.

Local deployment containers/services must not appear in the base 
`docker-compose.yml`.

Best practice is to have the same production service overridden in the 
`docker-compose.override.yaml` to use the development recipe/setup.

