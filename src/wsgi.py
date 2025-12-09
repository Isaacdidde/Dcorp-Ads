"""
WSGI Entrypoint for Render Deployment

Render runs this file with Gunicorn:
    gunicorn wsgi:app

This file must expose the Flask `app` object created by create_app().
"""

from app import create_app

# Create application
app = create_app()

# -----------------------------------------------------
# Local development only
# (Render / Gunicorn ignore this block)
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
