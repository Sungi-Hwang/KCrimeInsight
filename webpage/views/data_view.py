from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request, jsonify

import os
import math

from pathlib import Path

import pymysql
import pandas as pd
import yfinance as yf

from ..db import data_util
from ..db import ent_util
from ..db import analysis_util

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

# ---------------- ent_data 함수 ---------------- #
@data_bp.route("/ent_data", methods=['GET'])
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


# ---------------- crime_chart 함수 ---------------- #

@data_bp.route('/crime_chart', methods=['GET', 'POST'])
def crime_chart():

    crime_columns = ["강도", "교통범죄", "노동범죄", "도박범죄", "마약범죄", "병역범죄",
                     "보건범죄", "살인기수", "살인미수등", "선거범죄", "성풍속범죄", "안보범죄",
                     "절도범죄", "지능범죄", "특별경제범죄", "폭력범죄", "환경범죄"]

    selected_year = request.form.get('year', '전체')
    selected_crime = request.form.get('crime', '전체')

    rows2 = data_util.chart_crime()
    df = pd.DataFrame(rows2)

    if '연도' not in df.columns or '지역' not in df.columns:
        return "데이터 형식이 잘못되었습니다.", 500

    df = df[df['연도'] != '연도']  # 잘못된 헤더 제거
    df['연도'] = df['연도'].astype(int)

    # 연도 필터링
    if selected_year != '전체':
        df = df[df['연도'] == int(selected_year)]

    # 범죄 유형 필터링
    if selected_crime != '전체':
        df = df[['지역', selected_crime]]
    else:
        df = df[['지역'] + crime_columns]
        df = df.groupby('지역').sum().reset_index()

    # 차트용 데이터 생성
    chart_labels = df['지역'].tolist()
    chart_values = (
        df[crime_columns].sum(axis=1).tolist()
        if selected_crime == '전체'
        else df[selected_crime].tolist()
    )

    return render_template('data/crime_chart.html',
                           crime_columns=crime_columns,
                           labels=chart_labels,
                           values=chart_values,
                           selected_year=selected_year,
                           selected_crime=selected_crime)


@data_bp.route('/crime_chart2', methods=['GET', 'POST'])
def crime_chart2():

    crime_columns = ["강도", "교통범죄", "노동범죄", "도박범죄", "마약범죄", "병역범죄",
                     "보건범죄", "살인기수", "살인미수등", "선거범죄", "성풍속범죄", "안보범죄",
                     "절도범죄", "지능범죄", "특별경제범죄", "폭력범죄", "환경범죄"]

    selected_year = request.form.get('year', '전체')
    selected_region = request.form.get('region', '전체')

    data = data_util.chart_crime()
    df = pd.DataFrame(data)

    if df.empty:
        return "데이터가 없습니다", 500

    df = df[df['연도'] != '연도']
    df['연도'] = df['연도'].astype(int)

    if selected_year != '전체':
        df = df[df['연도'] == int(selected_year)]

    if selected_region != '전체':
        df = df[df['지역'] == selected_region]

    # 범죄 유형별 합계
    data = df[crime_columns].sum().to_dict()

    labels = list(data.keys())
    values = list(data.values())
    regions = sorted(data_util.get_all_regions())

    return render_template(
        'data/crime_chart2.html',
        labels=labels,
        values=values,
        regions=regions,
        selected_year=selected_year,
        selected_region=selected_region
    )

@data_bp.route('/get_crime_data_for_region', methods=['GET'])
def get_crime_data_for_region_route():
    region = request.args.get('region')
    year = request.args.get('year', '2022')

    if not region:
        return jsonify({'error': '지역 파라미터가 없습니다.'}), 400

    data = data_util.get_crime_data_for_region(region, year)

    if not data:
        return jsonify({'error': '데이터 없음'}), 404

    # labels와 values로 변환
    labels = list(data.keys())
    values = list(data.values())

    return jsonify({'labels': labels, 'values': values})


@data_bp.route('/correlation', methods=['GET', 'POST'])
def correlation_page():
    # 업종 목록
    ent_types = ['룸살롱', '노래클럽', '간이주점', '비어_바_살롱', '카바레', '기타']

    selected_type = request.form.get('types', '전체')
    selected_mode = request.form.get('mode', '절대값')

    if selected_mode == '비율':
        merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p, scatter_data = analysis_util.get_correlation_ratio_data(selected_type)
    else:
        merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p, scatter_data = analysis_util.get_correlation_data(selected_type)

    return render_template(
        'data/analysis_1.html',
        merged_data=merged_df.to_dict(orient='records'),
        pearson_corr=pearson_corr,
        pearson_p=pearson_p,
        spearman_corr=spearman_corr,
        spearman_p=spearman_p,
        scatter_data=scatter_data,
        ent_types=ent_types,
        selected_type=selected_type,
        selected_mode=selected_mode
    )
