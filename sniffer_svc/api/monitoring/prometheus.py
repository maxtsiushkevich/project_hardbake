from prometheus_client import Counter, Gauge, make_asgi_app


metrics = make_asgi_app()

calls = Counter('simple_counter', 'print nums of calls')
