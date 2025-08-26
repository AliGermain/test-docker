# README
<!-- TOC -->

- [README](#readme)
  - [Overview](#overview)
  - [Start developpement](#start-developpement)
  - [Stop developpement](#stop-developpement)
  - [General Docker commands](#general-docker-commands)
  - [Advanced Docker commands](#advanced-docker-commands)
    - [Clean commands](#clean-commands)
    - [Monitoring commands](#monitoring-commands)

<!-- /TOC -->

## Overview

This file give commands to start development with docker.

Require:
 - Docker installed.
 - Docker well configured, cf. **/etc/docker/deamon.json**
 - User in docker group to avoid sudo/su right

## Start developpement

Make these commands in this directory ```cd ./cicd/dev```.

Run container
```bash
# Put UID and GID in env file
echo -e "LOCAL_USER_ID=$(id -u)\nLOCAL_GROUP_ID=$(id -g)" > docker-compose.env;

# Build dev image
docker compose build
```

```bash
# Run containers
docker compose up
```

## Stop developpement

Make these commands in this directory ```cd ./cicd/dev```.

```bash
# Shutdown containers
docker-compose down
```

## General Docker commands

| Description | Commandes |
|- |- |
| Display images            | ```docker images``` |
| Remove image              | ```docker rmi myimages``` |
|- |- |
| Display all running containers | ```docker ps``` |
| Display all containers    | ```docker ps -a``` |
| Remove container          | ```docker rm mycontainer``` |
| Display info container    | ```docker inpect mycontainer``` |
| Display container ouput   | ```docker logs mycontainer``` |
| Stop container            | ```docker stop mycontainer``` |
| Kill container            | ```docker kill mycontainer``` |
|- |- |
| Connection as root | ```docker exec --user 0 -w / -it template-vue-python-backend_dev_web bash``` |
| Connection as www-data | ```docker exec --user www-data -w /var/www/html -it template-vue-python-backend_dev_web bash``` |
| Connection as postgres | ```docker exec --user postgres -it template-vue-python-backend_dev_db bash``` |
| Run composer install | ```docker exec --user www-data -w /var/www/html -it template-vue-python-backend_dev_web composer install ``` |


### Clean commands
```bash
# Stop all container
docker stop $(docker ps -a -q)

# Remove all container
docker rm $(docker ps -a -q)

# Delete all image with name or tag as "<none>"
docker rmi `docker images| egrep "<none>" |awk '{print $3}'`
```

### Monitoring commands

```bash
# Watch all container
watch -n 1 "docker ps -a"

# Watch all images
watch -n 1 "docker images"

# Watch all resources container
docker stats
```
