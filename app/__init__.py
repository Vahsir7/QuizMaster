from flask import Flask
from flask_migrate import Migrate
from .models import db
from dotenv import load_dotenv
import os

load_dotenv()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    from .student.routes import student_bp
    app.register_blueprint(student_bp)

    migrate.init_app(app, db)

    with app.app_context():
        from .models import Question, Exam, Attempt, Student, Admin, Subject, Chapter, SelectedAnswer
        db.create_all() 

        admin = Admin.query.get(1)
        if not admin:
            admin = Admin(
                AdminID = 1,
                Name = os.getenv('Admin_Username'),
                Email = os.getenv('Admin_email'),
                Password = os.getenv('Admin_Password')
            )
            db.session.add(admin)
            db.session.commit()
            print("admin created")
            print(admin)
        else:
            print(admin)

    return app

