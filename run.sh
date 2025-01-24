uv run \
opentelemetry-instrument \
--service_name app \
--traces_exporter console \
--metrics_exporter none \
--logs_exporter none \
gunicorn main:app --config gunicorn_conf.py
