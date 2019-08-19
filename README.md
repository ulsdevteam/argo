# argo
An API formatter which works against ElasticSearch.

## Proof of concept (with Docker installed)
1. pull down the repository
2. `cd argo`
3. `docker-compose up`
4. in a separate terminal `cd argo`
5. `docker-compose exec argo-web python manage.py test`
6.  visit `localhost:8000` to view the API responses
