# flexitkt

Flexit Customer Services (in norwegian KundeTjenester), which is the reason for the name KT.

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


# Setup microsoft authentication

Make sure `'django.contrib.sites'` is in `INSTALLED_APPS` and edit site instance through django admin, 
and set `domain` to `localhost:8000` for local server and `flexitkt.herokuapp.com` for deployed app

Create a [Azure AD App](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade). After you 
register the app, make sure you click on “Certificates & Secrets” and generate a new Client Secret.

When you are registering the app it will ask for a Redirect URI. This must match the absolute URL of your
 microsoft_auth:auth-callback view. By default this would be https://flexitkt.herokuapp.com/microsoft/auth-callback/ 
 for heroku app and http://localhost:8000 for local server.

This URL must be HTTPS unless your hostname is localhost. localhost can only be used if DEBUG is set to True.
 Microsoft only allows HTTP authentication if the hostname is localhost.
 
Use client id and secret from Azure AD App to configure environment variables.

Microsoft authentication can be disabled with setting 

# Deploy to heroku with docker container registry

Log in to registry, run

```
$> heroku container:login
```

Build the Docker image using dockerfile for production and tag it with the following format:

```
$> docker build -f Dockerfile.prod -t registry.heroku.com/flexitkt/web .
```

IMPORTANT !!! Use `Dockerfile.stg` when deploying to staging

Push the image to the registry:

```
$> docker push registry.heroku.com/flexitkt/web
```

Release the image:
```
$> heroku container:release -a flexitkt web
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
docker build -f Dockerfile.stg -t registry.heroku.com/flexitkt/web . && docker push registry.heroku.com/flexitkt/web && heroku container:release -a flexitkt web && heroku run python manage.py migrate
```

To deploy to `flexitkt-production` just replace in the above commands `flexitkt` with `flexitkt-production`

# Form warning settings

For displaying warnings if input value in the form is out of sanity or expectation limits we use 
model `FlexitFormWarningSettings`. At the moment the only place where we utilize this functionality is 
PriceEstimate widget. To set it up an instance of `FlexitFormWarningSettings` needs to be created with the limits.
The easiest way to do so is to run management script 
```
$> python manage.py create_initial_form_warning_settings_if_not_exist
```
the values can be edited afterwards through django admin
