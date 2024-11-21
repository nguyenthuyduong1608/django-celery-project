
## RUN DOCKER EVN

### Build docker compose
docker-compose up --build

### Check if Django app is accessible
docker-compose logs web

### Run Django Migrations
docker-compose run web python manage.py migrate

### Starting development server at http://localhost:8000/


## RUN SOURCE CODE

### Migrate initial data
python manage.py migrate

### Run source code
python manage.py runserver
