from flask import Flask
from flask import render_template

from .views import main_view, auth_view, data_view

def create_app():           # Flask가 웹 애플리케이션을 시작할 때 자동으로 호출하는 함수

    app = Flask(__name__)   # web application 만들기
    app.config['SECRET_KEY'] = 'crime-Araboja'

    app.register_blueprint(main_view.main_bp)
    app.register_blueprint(auth_view.auth_bp)
    app.register_blueprint(data_view.data_bp)

    return app