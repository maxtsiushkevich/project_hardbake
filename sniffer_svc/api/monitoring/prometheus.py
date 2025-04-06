from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(should_respect_env_var=True, env_var_name="ENABLE_METRICS")

metrics = make_asgi_app()
