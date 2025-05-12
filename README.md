## It is a powerful component easy-customizable intrusion detection system.

### To generate keys for Auth
``` openssl ecparam -genkey -name prime256v1 -noout -out private_key.pem ```

``` openssl ec -in private_key.pem -pubout -out public_key.pem ```

### Default user for Auth
username: ``admin``

password: ``admin``

### Deploy from Docker-compose 
``docker-compose -p project up -d ``

### Dashboard for Grafana 
Dashboard JSON in ``/grafana/grafana_dashboard.json``

## Services API
Просмотр с localhost
+ Модуль перехвата трафика [API](http://localhost:8000/docs)
+ Модуль предоставления информации о системе хоста [API](http://localhost:8001/docs)
+ Модуль обработки сетевых пакетов [API](http://localhost:8002/docs)
+ Модуль обработки данных для моделей машинного обучения [API](http://localhost:8003/docs)
+ Модуль тренировки моделей машинного обучения [API](http://localhost:8004/docs)
+ Модуль обнаружения угроз [API](http://localhost:8005/docs)
+ Модуль оповещения об обнаруженных угрозах [API](http://localhost:8006/docs)
+ Сервис авторизации [API](http://localhost:8008/docs)