import os
from flask import Flask
from flask_wtf import CSRFProtect # type: ignore
from flask_login import LoginManager # type: ignore
from flask_migrate import Migrate # type: ignore
from dotenv import load_dotenv # type: ignore
from pkg.config import Appconfig


csrf = CSRFProtect()

def create_app():
    from pkg.models import db

    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__,instance_relative_config=True) 
    app.config.from_object(Appconfig) #TO MAKE THE CONFIG ITEMS CREATED IN PKG/CONFIG.PY AVAILABLE
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Load SECRET_KEY from environment variable
    app.config.from_pyfile('config.py', silent=True)
    app.config['UPLOAD_FOLDER'] = 'pkg/static/uploads'

    db.init_app(app)
    csrf.init_app(app)
    migrate = Migrate(app,db)
    
    app.register_blueprint(users_routes.users_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

# from pkg import forms, user_routes, admin_routes, dbroutes
from pkg import users_routes
