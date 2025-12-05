# import os

# def load_config(app, overrides):
#     if os.path.exists(os.path.join('./App', 'custom_config.py')):
#         app.config.from_object('App.custom_config')
#     else:
#         app.config.from_object('App.default_config')
#     app.config.from_prefixed_env()
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['TEMPLATES_AUTO_RELOAD'] = True
#     app.config['PREFERRED_URL_SCHEME'] = 'https'
#     app.config['UPLOADED_PHOTOS_DEST'] = "App/uploads"
#     app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
#     app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
#     app.config["JWT_COOKIE_SECURE"] = True
#     app.config["JWT_COOKIE_CSRF_PROTECT"] = False
#     app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
#     for key in overrides:
#         app.config[key] = overrides[key]

import os

def load_config(app, overrides):
    if os.path.exists(os.path.join('./App', 'custom_config.py')):
        app.config.from_object('App.custom_config')
    else:
        app.config.from_object('App.default_config')

    app.config.from_prefixed_env()

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['UPLOADED_PHOTOS_DEST'] = "App/uploads"

    # JWT CONFIG
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]

    # For *local dev* on HTTP, this MUST be False
    app.config["JWT_COOKIE_SECURE"] = False

    # Explicitly allow cookies everywhere
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/"

    # Keep CSRF simple for now
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    # Optional but nice:
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"

    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'

    for key in overrides:
        app.config[key] = overrides[key]