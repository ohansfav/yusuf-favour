from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from routes.lecturer import lecturer_bp
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')

    from routes.hod import hod_bp
    app.register_blueprint(hod_bp, url_prefix='/hod')

    from routes.student import student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    from routes.registry import registry_bp
    app.register_blueprint(registry_bp, url_prefix='/registry')

    # Create tables
    with app.app_context():
        db.create_all()

    return app
