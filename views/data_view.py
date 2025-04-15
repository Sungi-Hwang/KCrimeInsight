from flask import Blueprint
from flask import render_template, redirect, url_for 
from flask import request

import os
from pathlib import Path
import pandas as pd

from ..db import data_util
from ..db import data_util2

data_bp = Blueprint("data", __name__, url_prefix="/data")

def get_display_pages(current_page, total_pages, display_range=5):
    pages = []

    # 항상 첫 페이지는 보여줌
    pages.append(1)

    # 중간 페이지 계산
    start = max(2, current_page - display_range // 2)
    end = min(total_pages - 1, current_page + display_range // 2)

    # 범위 조정
    if start > 2:
        pages.append("...")

    for p in range(start, end + 1):
        pages.append(p)

    if end < total_pages - 1:
        pages.append("...")

    # 마지막 페이지는 항상 보여줌 (총 페이지가 1보다 클 경우)
    if total_pages > 1:
        pages.append(total_pages)

    return pages

@data_bp.route("/crime_data", methods=['GET'])
def crime_data():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = data_util.select_crime_data(offset=offset, limit=per_page)
    columns = data_util.get_crime_data_columns()
    df_crime_data = pd.DataFrame(rows, columns=columns)

    total_count = data_util.count_crime_data()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/crime_data.html',
        df=df_crime_data,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        display_pages=display_pages
    )



@data_bp.route("/crime_data2", methods=['GET'])
def crime_data2():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = data_util2.select_entertain_bar(offset=offset, limit=per_page)
    columns = data_util2.get_entertain_bar_columns()
    df_entertain_bar = pd.DataFrame(rows, columns=columns)

    total_count = data_util2.count_entertain_bar()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/crime_data2.html',
        df=df_entertain_bar,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        display_pages=display_pages
    )