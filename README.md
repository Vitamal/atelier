# atelier

Atelier Clothes Making Services.

# styling

To build css files from source, run
 
```
$> ievv buildstatic
```

To work with styling, run in "watch" mode 
```
$> ievv buildstatic -w
```
 This will update build in real time.

# Run local server with docker

Use [docker-compose](https://docs.docker.com/compose/) when working on this project. 

To build a container, run
```
$> docker-compose build
```

To get server started, run
```
$> docker-compose up
```

To run management commands, run bash in the docker environment with:

```
$> docker exec -it web sh
```

In the prompt that appears, you should be able to run e.g

```
python manage.py migrate
# or
python manage.py createsuperuser
```

To make data fixtures for local development database, first dump data, and then copy
the created file from the docker container to local file system with these commands:

```
# In bash running in the docker environment:
python manage.py dumpdata > development_database.json

# Outside the docker environment:
docker cp web:/web/development_database.json development_database.json
```

# Working with translations

To generate messages for translation in `.py` files run 
```
python manage.py makemessages -l nb
```

To generate messages for translation in `.js` files first *always* run

```commandline
ievv buildstatic 
``` 
to generate jsbuild for translation sources and afterwards run
```
python manage.py makemessages -l nb -d djangojs
```
and after translating run 
```commandline
python manage.py compilemessages
```


# Deploy to heroku with docker container registry

Log in to registry, run

```
$> heroku container:login
```

Build the Docker image using dockerfile for production and tag it with the following format:

```
$> docker build -f Dockerfile.prod -t registry.heroku.com/atelier/web .
```

IMPORTANT !!! Use `Dockerfile.stg` when deploying to staging

Push the image to the registry:

```
$> docker push registry.heroku.com/atelier/web
```

Release the image:
```
$> heroku container:release -a atelier web
```

Migrate database if needed:
```
$> heroku run python manage.py migrate
```

Until further notice we also need to start `rqworker` manually by running
```
heroku run python manage.py rqworker
```

Or run it as a one-liner
```
docker build -f Dockerfile.stg -t registry.heroku.com/atelier/web . && docker push registry.heroku.com/atelier/web && heroku container:release -a atelier web && heroku run python manage.py migrate
```

To deploy to `atelier-production` just replace in the above commands `atelier` with `atelier-production`

# Form warning settings

For displaying warnings if input value in the form is out of sanity or expectation limits we use 
model `AtelierFormWarningSettings`. At the moment the only place where we utilize this functionality is 
PriceEstimate widget. To set it up an instance of `AtelierFormWarningSettings` needs to be created with the limits.
The easiest way to do so is to run management script 
```
$> python manage.py create_initial_form_warning_settings_if_not_exist
```
the values can be edited afterwards through django admin
