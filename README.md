# Powerful component easy-customizable intrusion detection system.

## User guides
[User guide](UserGuide_EN.pdf)
[Руководство пользователя](UserGuide_RU.pdf)

## Description 
It is a modular intrusion detection system based on machine learning. It implements a full cycle of data collection and processing. Each module can be used separately as a container. Additional modules (report generators, etc.) can also be easily added.

## Deploy from Docker-compose 
``docker-compose -p project up -d ``

## Enviroment

### Keys for Auth
Authentication uses a pair of private and public keys. Only the authentication service should have access to the private key. Other modules should only have access to the public key.

``` bash
 openssl ecparam -genkey -name prime256v1 -noout -out private_key.pem 
 ```

``` bash
 openssl ec -in private_key.pem -pubout -out public_key.pem 
 ```
### RabbitMQ
The required RabbitMQ configuration is contained in ``rabbitmq/rabbit_conf.json``. When running via docker-compose, it will be automatically applied.

### Dashboard for Grafana 
Import dashboards from Grafana. If you already have Grafana in your infrastructure, remove it from the docker-compose file.

Dashboard JSON in ``/grafana/grafana_dashboard.json``

### Default user for Auth
It is recommended to create your own admin account and delete the starter account.

``username: admin``

``password: admin``

### Deploy from Docker-compose 
``` bash
docker-compose -p project up -d 
```

### Dashboard for Grafana 
Import dashboards from Grafana. If you already have Grafana in your infrastructure, remove it from the docker-compose file.

Dashboard JSON in ``/grafana/grafana_dashboard.json``
