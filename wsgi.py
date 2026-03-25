from app import create_app

# Gunicorn expects a module-level `app` callable named `wsgi:app`.
app = create_app()

