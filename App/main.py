
import os
from flask import Flask, render_template
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS

from App.database import init_db
from App.config import load_config

from App.controllers import (
    setup_jwt,
    add_auth_context
)
from App.api.errors import register_error_handlers
from App.views import views, setup_admin


from App.controllers.initialize import initialize


def add_views(app):
    for view in views:
        app.register_blueprint(view)


def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')

    
    load_config(app, overrides)
    CORS(app)
    add_auth_context(app)

  
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)

    
    add_views(app)
    init_db(app)
    jwt = setup_jwt(app)
    setup_admin(app)
    register_error_handlers(app)

    @jwt.invalid_token_loader
    @jwt.unauthorized_loader
    def custom_unauthorized_response(error):
        return render_template('401.html', error=error), 401

    app.app_context().push()

    from App.controllers.initialize import initialize

    is_testing = app.config.get("TESTING", False)
    auto_init = os.getenv("BREADVAN_AUTO_INIT", "1") == "1"

    if not is_testing and auto_init:
        try:
            app.logger.info("Auto-initializing database & seed data...")
            initialize()
        except Exception as e:
            app.logger.error(f"Auto-init failed: {e}")

    return app