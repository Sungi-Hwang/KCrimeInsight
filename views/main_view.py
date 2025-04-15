from flask import Blueprint
from flask import render_template

main_bp = Blueprint('main', __name__, url_prefix="/")

@main_bp.route("/", methods=['GET'])
def index():
    return render_template('index.html')    # 홈페이지 들어가면 처음 보여주는 기본 위치 (템플릿에 존재)