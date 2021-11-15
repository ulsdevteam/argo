# argo

API middleware which provides a simplified API of data stored in Elasticsearch.

argo is part of [Project Electron](https://github.com/RockefellerArchiveCenter/project_electron), an initiative to build sustainable, open and user-centered infrastructure for the archival management of digital records at the [Rockefeller Archive Center](http://rockarch.org/).

[![Build Status](https://app.travis-ci.com/RockefellerArchiveCenter/argo.svg?branch=base)](https://app.travis-ci.com/RockefellerArchiveCenter/argo)

## Setup

Install [git](https://git-scm.com/) and clone the repository

    $ git clone git@github.com:RockefellerArchiveCenter/argo.git

Install [Docker](https://store.docker.com/search?type=edition&offering=community) and run docker-compose from the root directory

    $ cd argo
    $ docker-compose up

Once the application starts successfully, you should be able to access the application in your browser at `http://localhost:8000`

When you're done, shut down docker-compose

    $ docker-compose down

Or, if you want to remove all data

    $ docker-compose down -v


## Configuring

Argo configurations are stored in `/argo/config.py`. This file is excluded from version control, and you will need to update this file with values for your local instance.

The first time the container is started, the example config file (`/argo/config.py.example`) will be copied to create the config file if it doesn't already exist.


## Routes

| Method | URL | Parameters | Response  | Behavior  |
|--------|-----|---|---|---|
|GET|/agents||200|Returns data about Agents|
|GET|/collections||200|Returns data about Collections|
|GET|/objects||200|Returns data about Objects|
|GET|/terms||200|Returns data about Terms|
|GET|/search||200|Returns search data|
|GET|/schema/||200|Returns the OpenAPI schema|


## Development

This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.


## License

This code is released under an [MIT License](LICENSE).
