from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request, jsonify

import os
import math

from pathlib import Path

import pandas as pd
import yfinance as yf

from ..db import data_util
from ..db import ent_util

data_bp = Blueprint("data", __name__, url_prefix="/data")


# ---------------- 페이징 처리 함수 ---------------- #

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


# ---------------- crime_data_11_22 함수 ---------------- #
@data_bp.route("/crime_data_11_22", methods=['GET'])
def crime_data_11_22():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = data_util.select_crime_data_11_22(offset=offset, limit=per_page)
    columns = data_util.get_crime_data_11_22_columns()
    df_crime_data_11_22 = pd.DataFrame(rows, columns=columns)

    total_count = data_util.count_crime_data_11_22()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/crime_data_11_22.html',
        df=df_crime_data_11_22,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        display_pages=display_pages
    )

# ---------------- crime_data_23 함수 ---------------- #
@data_bp.route("/crime_data_23", methods=['GET'])
def crime_data_23():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = data_util.select_crime_data_23(offset=offset, limit=per_page)
    columns = data_util.get_crime_data_23_columns()
    df_crime_data_23 = pd.DataFrame(rows, columns=columns)

    total_count = data_util.count_crime_data_23()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/crime_data_23.html',
        df=df_crime_data_23,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        display_pages=display_pages
    )

# ---------------- ent_data 함수 ---------------- #
@data_bp.route("/ent_data ", methods=['GET'])
def ent_data():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = ent_util.select_ent_data(offset=offset, limit=per_page)
    columns = ent_util.get_ent_data_columns()
    df_ent_data = pd.DataFrame(rows, columns=columns)

    total_count = ent_util.count_ent_data()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/ent_data.html',
        df=df_ent_data,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        display_pages=display_pages
    )


