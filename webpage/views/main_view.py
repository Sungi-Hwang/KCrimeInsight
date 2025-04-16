from flask import Blueprint, render_template
import pandas as pd
from ..db import data_util  # 이거 import 추가

main_bp = Blueprint('main', __name__, url_prefix="/")

@main_bp.route("/", methods=['GET'])
def index():
    crime_columns = ["강도", "교통범죄", "노동범죄", "도박범죄", "마약범죄", "병역범죄",
                     "보건범죄", "살인기수", "살인미수등", "선거범죄", "성풍속범죄", "안보범죄",
                     "절도범죄", "지능범죄", "특별경제범죄", "폭력범죄", "환경범죄"]

    rows = data_util.chart_crime()
    df = pd.DataFrame(rows)
    df = df[df['연도'] != '연도']
    df['연도'] = df['연도'].astype(int)
    df = df[df['연도'] == 2022]

    # crime_chart 데이터
    chart_labels = df['지역'].tolist()
    chart_values = df[crime_columns].sum(axis=1).tolist()

    # crime_chart2 데이터 (범죄 유형별 합계)
    crime_sum = df[crime_columns].sum().to_dict()
    type_labels = list(crime_sum.keys())
    type_values = list(crime_sum.values())

    return render_template('index.html',
                           labels=chart_labels,
                           values=chart_values,
                           type_labels=type_labels,
                           type_values=type_values)
