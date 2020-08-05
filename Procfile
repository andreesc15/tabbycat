# WSGI server handles the standard django routes; optimised for high performance
http: gunicorn --bind :8000 --workers 4 --threads 2 tabbycat.wsgi:application

# ASGI server handles the asychronous routes (websockets)
websocket: daphne -b 0.0.0.0 -p 5000 tabbycat.asgi:application

# Workers
worker: python tabbycat/manage.py runworker notifications portal adjallocation venues
