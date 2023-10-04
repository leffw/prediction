from os import environ

# API configuration.
API_HOST = environ.get("API_HOST", "0.0.0.0")
API_PORT = int(environ.get("API_PORT", 3462))

# JWT configuration.
API_JWT_SECRET_KEY = environ.get("API_JWT_SECRET_KEY")
if not (API_JWT_SECRET_KEY):
    raise ValueError("Environment variable 'API_JWT_SECRET_KEY' is invalid.")