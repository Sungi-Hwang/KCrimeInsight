import matplotlib
matplotlib.use('Agg')

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request, jsonify

from pathlib import Path

import os
import math

import pymysql
import pandas as pd
import yfinance as yf
import io, base64
import matplotlib.pyplot as plt
import seaborn as sns

from ..db import data_util
from ..db import ent_util
from ..db import analysis_util
from ..db import variables_util
from ..db import crime_final_kyle_util
from ..db import merged_kyle_util

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


# ---------------- 지역처리 함수 ---------------- #

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


# ---------------- 유흥주점 페이지 함수 ---------------- #

@data_bp.route('/correlation', methods=['GET', 'POST'])
def correlation_page():
    selected_type = request.form.get('ent_type', '전체')
    selected_mode = request.form.get('mode', '절대값')

    ent_types = ['전체', '룸살롱', '노래클럽', '비어_바_살롱', '카바레', '간이주점', '기타']

    if selected_mode == '비율':
        result = analysis_util.get_correlation_ratio_data(selected_type)
    else:
        result = analysis_util.get_correlation_data(selected_type)

    if result[0] is None:
        merged_df = pd.DataFrame()
        pearson_corr = pearson_p = spearman_corr = spearman_p = 0
        scatter_data = []
        regression_line = []
        max_x = 1
        max_y = 1
    else:
        merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p, scatter_data, regression_line = result
        max_x = max([p['x'] for p in scatter_data], default=1) * 1.2
        max_y = max([p['y'] for p in scatter_data], default=1) * 1.2

    return render_template(
        'data/analysis_1.html',
        merged_data=merged_df.to_dict(orient='records'),
        pearson_corr=pearson_corr,
        pearson_p=pearson_p,
        spearman_corr=spearman_corr,
        spearman_p=spearman_p,
        scatter_data=scatter_data,
        regression_line=regression_line,
        ent_types=ent_types,
        selected_type=selected_type,
        selected_mode=selected_mode,
        max_x=max_x,
        max_y=max_y
    )

# ---------------- 비율 페이지 함수 ---------------- #
@data_bp.route('/correlation_ratio', methods=['GET', 'POST'])
def correlation_ratio_page():
    merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p, scatter_data, regression_line = analysis_util.get_correlation_ratio_data()

    max_x = max([p['x'] for p in scatter_data]) * 1.2
    max_y = max([p['y'] for p in scatter_data]) * 1.2

    return render_template('data/analysis_1.html',
                           merged_data=merged_df.to_dict(orient='records'),
                           pearson_corr=pearson_corr,
                           pearson_p=pearson_p,
                           spearman_corr=spearman_corr,
                           spearman_p=spearman_p,
                           scatter_data=scatter_data,
                           regression_line=regression_line,
                           max_x=max_x, max_y=max_y)

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


# ---------------- variables_data 함수 ---------------- #
@data_bp.route("/variables_data", methods=['GET'])
def variables_data():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)
    offset = (page - 1) * per_page

    rows = variables_util.select_variables_data(offset=offset, limit=per_page)
    columns = variables_util.get_variables_data_columns()
    df_ent_data = pd.DataFrame(rows, columns=columns)

    total_count = variables_util.count_variables_data()
    total_pages = (total_count + per_page - 1) // per_page  # 올림 계산

    display_pages = get_display_pages(page, total_pages)
    
    return render_template(
        'data/variables.html',
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
    selected_mode = request.form.get('mode', '절대값')

    chart_labels = []
    chart_values = []

    if selected_mode == '비율':
        # 비율 모드일 때 데이터 불러오기
        df = data_util.chart_crime_ratio(selected_year, selected_crime)
        if df.empty:
            return "데이터 없음", 500

        chart_labels = df['지역'].tolist()

        if selected_crime == '전체':
            df['전체비율'] = df[[f"{col}비율" for col in crime_columns]].sum(axis=1)
            chart_values = df['전체비율'].fillna(0).tolist()
        else:
            col_name = f"{selected_crime}비율"
            if col_name not in df.columns:
                return f"컬럼 {col_name} 없음", 500
            chart_values = df[col_name].fillna(0).tolist()

    else:   
        # 절대값 모드
        rows2 = data_util.chart_crime()
        df = pd.DataFrame(rows2)

        if '연도' not in df.columns or '지역' not in df.columns:
            return "데이터 형식이 잘못되었습니다.", 500

        df = df[df['연도'] != '연도']
        df['연도'] = df['연도'].astype(int)

        if selected_year != '전체':
            df = df[df['연도'] == int(selected_year)]

        if selected_crime != '전체':
            df = df[['지역', selected_crime]]
            df = df.groupby('지역').sum().reset_index()  # 추가
        else:
            df = df[['지역'] + crime_columns]
            df = df.groupby('지역').sum().reset_index()  # 추가

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
                           selected_crime=selected_crime,
                           selected_mode=selected_mode)


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

    return render_template('data/crime_chart2.html',
                           labels=labels,
                           values=values,
                           regions=regions,
                           selected_year=selected_year,
                           selected_region=selected_region)

@data_bp.route('/crime_chart3', methods=['GET', 'POST'])
def crime_chart3():

    variables_columns = ['경찰관수', '다문화 혼인 비중(％)', '음주 표준화율 (％)', '실업률 (％)', '1인 가구 비율']
    crimes_columns = ['강간_통합', '강력범죄_통합', '도박_통합', '방화_통합', '사기_통합', '살인_통합',
                    '절도_통합', '폭력_통합', '협박_통합']
    
    labels, values = [], []
    value1 = value2 = ""

    if request.method == 'POST':
        value1 = request.form.get('value1')
        value2 = request.form.get('value2')

        rows_var = variables_util.variables_data()
        rows_crimes = crime_final_kyle_util.crimes_data()
        df_var = pd.DataFrame(rows_var)
        df_crimes = pd.DataFrame(rows_crimes)

        df_var['연도'] = df_var['연도'].astype(int)
        df_crimes['연도'] = df_crimes['연도'].astype(int)

        filt_var_df = df_var[df_var['연도'].isin([2021, 2022, 2023])]
        filt_crimes_df = df_crimes[df_crimes['연도'].isin([2021, 2022, 2023])]

        df = pd.merge(filt_var_df, filt_crimes_df, on=['region', '연도'], how='left')

        result_col = f'{value1}_VS_{value2}'
        correlation_df = df.groupby('region').apply(lambda g: g[value1].corr(g[value2])
        ).reset_index(name=result_col)

        labels = correlation_df['region'].tolist()
        values = correlation_df[result_col].tolist()

    return render_template(
        'data/crime_chart3.html',
        crimes_columns=crimes_columns,
        variables_columns=variables_columns,
        labels=labels,
        values=values,
        value1=value1,
        value2=value2)

# ---------------- 히트맵 함수 ---------------- #
@data_bp.route('/crime_heatmap', methods=['GET', 'POST'])
def crime_heatmap():

    # 데이터 불러오기
    rows_var = merged_kyle_util.merged_data()
    df = pd.DataFrame(rows_var)
    df['연도'] = df['연도'].astype(int)
    years = sorted(df['연도'].unique())

    selected_year = "전체"
    heatmaps = []

    if request.method == 'POST':
        selected_year = request.form.get('selected_year')

        if selected_year == "전체":
            # 🔁 변화율 기반 상관관계 계산
            df_sorted = df.sort_values(by=['region', '연도']).reset_index(drop=True)
            pct_change_df = df_sorted.groupby('region').apply(
                lambda x: x.drop(columns=['region']).set_index('연도').pct_change()
            ).reset_index()
            pct_change_df['region'] = df_sorted['region']

            numeric_pct = pct_change_df.drop(columns=['region', '연도']).dropna()
            cor_change = numeric_pct.corr()

            # 히트맵 그리기
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
            plt.figure(figsize=(10, 8))
            sns.heatmap(cor_change, annot=True, fmt=".2f", cmap="coolwarm")
            plt.title("3개년 변화율 기반 상관관계 히트맵")
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            heatmaps.append(("3개년 변화율", img_base64))

        else:
            # 특정 연도에 대한 상관관계
            year = int(selected_year)
            df_year = df[df['연도'] == year].drop(columns=['region'])
            corr = df_year.corr()

            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
            plt.title(f"{year}년 상관관계 히트맵")
            plt.xticks(rotation=45)
            plt.yticks(rotation=0)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            heatmaps.append((year, img_base64))

    return render_template(
        'data/crime_heatmap.html',
        years=years,
        selected_year=selected_year,
        heatmaps=heatmaps
    )
