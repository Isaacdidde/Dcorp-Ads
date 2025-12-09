"""
WSGI Entrypoint for Production Servers

Used by:
- Gunicorn
- uWSGI
- Nginx + Gunicorn stack
- Railway / Render / Heroku
- Docker deployments

This file should remain extremely small and stable.
"""

from app import create_app

# Create Flask application using the factory pattern
app = create_app()


# -----------------------------------------------------
# LOCAL DEV ENTRYPOINT ONLY
# (Production servers ignore this block)
# -----------------------------------------------------
if __name__ == "__main__":
    # Running directly = development mode only
    # Production uses gunicorn:
    #   gunicorn --bind 0.0.0.0:8000 wsgi:app
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )



#for Gunicorn or uWSGI
# """
# WSGI Entrypoint for Render Deployment

# Render runs this file with Gunicorn:
#     gunicorn wsgi:app

# This file must expose the Flask `app` object created by create_app().
# """

# from app import create_app

# # Create Flask application using factory pattern
# app = create_app()

# # -----------------------------------------------------
# # Local Development Only
# # (Render ignores this block)
# # -----------------------------------------------------
# if __name__ == "__main__":
#     # Running via: python wsgi.py
#     # Use environment-controlled debug from settings.py
#     app.run(
#         host="0.0.0.0",
#         port=5000
#     )
