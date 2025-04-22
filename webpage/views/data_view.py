import matplotlib
matplotlib.use('Agg')

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request, jsonify
from flask import send_file
from datetime import datetime
#from webpage.model.predictor import predict_one

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import os, io, base64, re, math
import plotly.io as pio
import plotly.express as px

from pathlib import Path
from ..db import data_util
from ..db import ent_util
from ..db import analysis_util
from ..db import variables_util
from ..db import crime_final_kyle_util
from ..db import merged_kyle_util


data_bp = Blueprint("data", __name__, url_prefix="/data")


@data_bp.route('/prediction_graph')
def prediction_graph():
    graph_path = os.path.join('webpage', 'static', 'images', 'graphs', 'graph_1.png')

    # 만약 첫 번째 그래프 이미지가 존재하면 학습/생성 생략
    if os.path.exists(graph_path):
        print("✅ 기존 그래프 존재 — 바로 페이지 렌더링")
        graph_count = len([name for name in os.listdir(os.path.dirname(graph_path)) if name.startswith('graph_') and name.endswith('.png')])
        return render_template('data/prediction_graph.html', graph_count=graph_count)


    # 데이터 불러오기 및 모델 결과 계산
    df_crime = pd.DataFrame(data_util.chart_crime())
    df_var = pd.DataFrame(variables_util.variables_data())
    df_var = df_var.rename(columns={'region': '지역'})
    merged_df = pd.merge(df_var, df_crime, on=['연도', '지역'], how='inner')

    X = merged_df[['경찰관수', '다문화 혼인 비중(％)', '음주 표준화율 (％)', '실업률 (％)', '1인 가구 비율']]
    y = merged_df.drop(columns=['연도', '지역'] + X.columns.tolist())

    from sklearn.linear_model import LinearRegression
    from sklearn.multioutput import MultiOutputRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = MultiOutputRegressor(LinearRegression())
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    comparison_df = y_test.reset_index(drop=True).copy()
    for i, col in enumerate(y.columns):
        comparison_df[f'{col}_예측'] = y_pred[:, i]

    mae_r2_per_crime = {
        col: {
            'mae': round(np.mean(np.abs(comparison_df[col] - comparison_df[f'{col}_예측'])), 2),
            'r2': round(r2_score(comparison_df[col], comparison_df[f'{col}_예측']), 2)
        }
        for col in y.columns
    }

    # 그래프 생성 및 저장
    crime_columns = list(y.columns)
    chunks = [crime_columns[i:i + 2] for i in range(0, len(crime_columns), 2)]  # 좌우 2개씩 나열

    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

    for idx, subset in enumerate(chunks):
        print(f"🔄 루프 {idx+1}: {subset}")
        fig, axs = plt.subplots(1, 2, figsize=(22, 10))
        for i, col in enumerate(subset):
            axs[i].scatter(comparison_df[col], comparison_df[f'{col}_예측'],s=100, alpha=0.7, color='steelblue')
            axs[i].plot([comparison_df[col].min(), comparison_df[col].max()],
                       [comparison_df[col].min(), comparison_df[col].max()], 'r--')
            axs[i].set_title(f"{col}", fontsize=20)
            axs[i].set_xlabel("실제값", fontsize=20)
            axs[i].set_ylabel("예측값", fontsize=20)
            axs[i].tick_params(axis='both', labelsize=18)

            mae = mae_r2_per_crime[col]['mae']
            r2 = mae_r2_per_crime[col]['r2']
            axs[i].text(0.5, -0.12, f"MAE: {mae:.2f} | R²: {r2:.2f}",
                        transform=axs[i].transAxes, ha='center', fontsize=18)
        # ❗ 남은 subplot 지우기 (예: 마지막에 하나만 있을 때)
        for j in range(len(subset), len(axs)):
            fig.delaxes(axs[j])

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        graph_path = os.path.join('webpage', 'static', 'images', 'graphs', f'graph_{idx+1}.png')
        # 이미지가 없을 때만 저장
        if not os.path.exists(graph_path):
            os.makedirs(os.path.dirname(graph_path), exist_ok=True)
            plt.savefig(graph_path)
            print(f"📁 저장됨: {graph_path}")
        else:
            print(f"✅ 이미 존재: {graph_path}")

        os.makedirs(os.path.dirname(graph_path), exist_ok=True)
        plt.savefig(graph_path)
        plt.close()

    print("📁 저장됨:", graph_path)

    return render_template('data/prediction_graph.html', graph_count=len(chunks))
    
    # return render_template('data/prediction_graph.html')


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
    active_tab = request.form.get("active_tab", "city")
    selected_type = request.form.get('ent_type', '전체')
    selected_mode = request.form.get('mode', '절대값')
    density_basis = request.form.get("density_basis", "area")
    ent_density_basis = request.form.get('ent_density_basis', 'area')
    crime_density_basis = request.form.get('crime_density_basis', 'area')
    remove_outliers = request.form.get('remove_outliers', 'false')

    result = analysis_util.get_density_correlation_data(
        selected_type, ent_density_basis, crime_density_basis, remove_outliers == 'true'
    )


    ent_types = ['룸살롱', '노래클럽', '비어_바_살롱', '카바레', '간이주점', '기타']

    if selected_mode == '비율':
        result = analysis_util.get_correlation_ratio_data(selected_type)
        if result[0] is None:
            merged_df = pd.DataFrame()
            pearson_corr = pearson_p = spearman_corr = spearman_p = 0
            scatter_data = []
            regression_line = []
            max_x = 1
            max_y = 1
        else:
            (merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p,
            scatter_data, regression_line) = result
            max_x = max([p['x'] for p in scatter_data], default=1) * 1.2
            max_y = max([p['y'] for p in scatter_data], default=1) * 1.2

    elif selected_mode == '밀집도':
        result = analysis_util.get_density_correlation_data(selected_type, ent_density_basis, crime_density_basis)                    
        if result[0] is None:
            merged_df = pd.DataFrame()
            pearson_corr = pearson_p = spearman_corr = spearman_p = 0
            scatter_data = []
            regression_line = []
            max_x = 1
            max_y = 1
        else:
            (merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p,
            scatter_data, regression_line, max_x, max_y) = result

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
            (merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p,
            scatter_data, regression_line) = result
            max_x = max([p['x'] for p in scatter_data], default=1) * 1.2
            max_y = max([p['y'] for p in scatter_data], default=1) * 1.2


    return render_template(
        'data/analysis_1.html',
        merged_data=merged_df if selected_mode == '밀집도' else merged_df.to_dict(orient='records'),
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
        max_y=max_y,
        active_tab=active_tab,
        density_basis=density_basis,
        ent_density_basis=ent_density_basis,
        crime_density_basis=crime_density_basis,
        remove_outliers=remove_outliers
    )

@data_bp.route('/get_density_chart_data', methods=['POST'])
def get_density_chart_data():
    selected_type = request.form.get('ent_type', '전체')
    ent_basis = request.form.get('ent_density_basis', 'area')
    crime_basis = request.form.get('crime_density_basis', 'area')
    remove_outliers = request.form.get('remove_outliers', 'false')

    result = analysis_util.get_density_correlation_data(
        selected_type, ent_basis, crime_basis, remove_outliers == 'true'
    )

    if result[0] is None:
        return jsonify({
            'scatter_data': [], 'regression_line': [],
            'pearson_corr': 0, 'spearman_corr': 0,
            'max_x': 1, 'max_y': 1
        })

    (merged_df, pearson_corr, pearson_p, spearman_corr, spearman_p,
    scatter_data, regression_line, max_x, max_y) = result

    return jsonify({
        'scatter_data': scatter_data,
        'regression_line': regression_line,
        'pearson_corr': pearson_corr,
        'pearson_p': pearson_p,
        'spearman_corr': spearman_corr,
        'spearman_p': spearman_p,
        'max_x': max_x,
        'max_y': max_y
    })

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

@data_bp.route('/crime_chart4', methods=['GET', 'POST'])
def crime_chart4():

    variables_columns = ['경찰관수', '다문화 혼인 비중(％)', '음주 표준화율 (％)', '실업률 (％)', '1인 가구 비율']
    crimes_columns = ['강간_통합', '강력범죄_통합', '도박_통합', '방화_통합', '사기_통합', '살인_통합',
                    '절도_통합', '폭력_통합', '협박_통합']
    
    value1 = value2 = ""

    if request.method == 'POST':
        value1 = request.form.get('value1')
        value2 = request.form.get('value2')

    return render_template(
        'data/crime_chart4.html',
        variables_columns=variables_columns,
        crimes_columns=crimes_columns,
        value1=value1,
        value2=value2,
        now=datetime.now().timestamp()
    )


@data_bp.route('/crime_chart4/image', methods=['GET'])  # 이미지 표시용은 GET만 쓰자
def crime_chart4_image():
    
    value1 = request.args.get('value1')
    value2 = request.args.get('value2')

    if not value1 or not value2:
        return "value1, value2 값이 필요합니다.", 400

    # 데이터 불러오기
    df_var = pd.DataFrame(variables_util.variables_data())
    df_crimes = pd.DataFrame(crime_final_kyle_util.crimes_data())

    df_var['연도'] = df_var['연도'].astype(int)
    df_crimes['연도'] = df_crimes['연도'].astype(int)

    df_var = df_var[df_var['연도'].isin([2021, 2022, 2023])]
    df_crimes = df_crimes[df_crimes['연도'].isin([2021, 2022, 2023])]

    df = pd.merge(df_var, df_crimes, on=['region', '연도'], how='left')

    value1_col = value1 + "_x" if value1 + "_x" in df.columns else value1
    value2_col = value2 + "_y" if value2 + "_y" in df.columns else value2

    # 상관계수 계산
    correlation_by_year = {}
    for year in [2021, 2022, 2023]:
        temp_df = df[df['연도'] == year]
        correlation_by_year[str(year)] = temp_df[value1_col].corr(temp_df[value2_col])
    correlation_by_year['전체 평균'] = df[value1_col].corr(df[value2_col])

    # 그래프 생성
    labels = list(correlation_by_year.keys())
    values = list(correlation_by_year.values())
    colors = ['skyblue', 'salmon', 'mediumseagreen', 'mediumpurple']

    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=colors)
    for bar in bars:
        yval = bar.get_height()
        plt.text( 
            bar.get_x() + bar.get_width() / 2,   # 막대 중앙 x
            yval / 2,                            # 막대 높이의 절반 (내부 중앙)
            f'{yval:.2f}',                       # 텍스트
            ha='center', va='center', fontsize=11, color='white', fontweight='bold'
            )

    plt.ylim(-1, 1)
    plt.axhline(0, color='gray', linestyle='--')
    plt.title(f"{value1} vs {value2} 연도별 상관관계")
    plt.ylabel("상관계수")
    plt.tight_layout()

    # 이미지로 반환
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

import pprint

@data_bp.route('/crime_corr', methods=['GET', 'POST'])
def crime_corr_page():
    variables_columns = ['경찰관수', '다문화 혼인 비중(％)', '음주 표준화율 (％)', '실업률 (％)', '1인 가구 비율']
    crimes_columns = ['강간_통합', '강력범죄_통합', '도박_통합', '방화_통합', '사기_통합', '살인_통합',
                      '절도_통합', '폭력_통합', '협박_통합']

    value1 = request.values.get("value1")
    value2 = request.values.get("value2")


    labels, values = [], []

    if value1 and value2:

        df_var = pd.DataFrame(variables_util.variables_data())
        df_crimes = pd.DataFrame(crime_final_kyle_util.crimes_data())


        df_var['연도'] = df_var['연도'].astype(int)
        df_crimes['연도'] = df_crimes['연도'].astype(int)

        df = pd.merge(df_var, df_crimes, on=['region', '연도'], how='left')


        value1_col = value1 + "_x" if value1 + "_x" in df.columns else value1
        value2_col = value2 + "_y" if value2 + "_y" in df.columns else value2


        corr_df = df.groupby('region').apply(
            lambda g: g[value1_col].corr(g[value2_col])
        ).reset_index(name='corr')

        labels = corr_df['region'].tolist()
        values = corr_df['corr'].tolist()

    return render_template(
        "data/crime_corr.html",
        variables_columns=variables_columns,
        crimes_columns=crimes_columns,
        value1=value1 or '',
        value2=value2 or '',
        labels=labels,
        values=values
    )

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



# ✅ Updated crime_insight_page with Plotly-based interactive charts
@data_bp.route("/insight", methods=["GET", "POST"])
def crime_insight_page():
    import pandas as pd, re
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.figure_factory as ff
    from ..db.data_util import get_population_data, get_crsis_code_data
    from ..model.predictor import CrimePredictor   # ← 새로 작성한 모듈
    import datetime
    import plotly.io as pio
    pio.templates.default = "plotly_white"
    # ─────────── 데이터 준비 ───────────
    df = get_population_data()
    detail_df = get_crsis_code_data()
    df.rename(columns={"year": "연도", "region": "지역"}, inplace=True)

    meta_cols = ["연도", "지역", "population"]
    crime_cols = [c for c in df.columns if c not in meta_cols]
    for c in crime_cols:
        df[f"{c}_rate"] = df[c] / df["population"] * 1e3
    rate_cols = [c for c in df.columns if c.endswith("_rate")]

    # ─────────── UI 선택값 ───────────
    crime_categories = detail_df["사용자정의분류"].tolist()
    selected_category = request.form.get("category", crime_categories[0])
    region_options = ["전국"] + sorted(df["지역"].unique())
    selected_region = request.form.get("region", "전국")

    # ─────────── 상관계수 히트맵 데이터 ───────────
    region_df = df.groupby("연도")[rate_cols].mean() if selected_region == "전국" else df[df["지역"] == selected_region][rate_cols]
    region_df = region_df.drop(columns=["연도"], errors="ignore")

    corr = region_df.corr()
    labels_raw = list(corr.columns)  # <─ 중요: 순서 보존용
    labels = [col.replace("_rate", " 발생률") for col in labels_raw]
    corr.columns = labels
    corr.index = labels

    fig_heatmap = ff.create_annotated_heatmap(
        z=corr.values.round(2),
        x=labels,
        y=labels,
        colorscale='RdBu',
        zmin=-1,
        zmax=1,
        showscale=True,
        annotation_text=corr.values.round(2)
    )
    fig_heatmap.update_layout(
    autosize=True,
    margin=dict(l=80, r=20, t=30, b=80),
    height=700,
    xaxis=dict(tickangle=45)
    )
    heatmap_html = fig_heatmap.to_html(full_html=False, include_plotlyjs=True)

    # ─────────── 라벨 매핑 ───────────
    rate_label_map = {col: col.replace("_rate", " 발생률") for col in rate_cols}
    label_to_col = {v: k for k, v in rate_label_map.items()}
    trend_labels = list(label_to_col.keys())

    selected_trend1 = request.form.get("trend_crime1", trend_labels[0])
    selected_trend2 = request.form.get("trend_crime2", trend_labels[1] if len(trend_labels) > 1 else trend_labels[0])
    trend_col1 = label_to_col[selected_trend1]
    trend_col2 = label_to_col[selected_trend2]

    line_df = df.groupby("연도")[[trend_col1, trend_col2]].mean().reset_index() if selected_region == "전국" else df[df["지역"] == selected_region][["연도", trend_col1, trend_col2]]

    # ─────────── 이중 y축 Plotly ───────────
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Scatter(
        x=line_df["연도"], y=line_df[trend_col1], name=selected_trend1,
        yaxis="y1", mode="lines+markers"
    ))
    fig_compare.add_trace(go.Scatter(
        x=line_df["연도"], y=line_df[trend_col2], name=selected_trend2,
        yaxis="y2", mode="lines+markers", line=dict(dash="dot")
    ))
    fig_compare.update_layout(
        title="이중 Y축 범죄 추이",
        xaxis=dict(title="연도"),
        yaxis=dict(title=selected_trend1),
        yaxis2=dict(title=selected_trend2, overlaying='y', side='right')
    )
    compare_trend_html = fig_compare.to_html(full_html=False, include_plotlyjs=False)

    # ─────────── 단일 범죄 Plotly ───────────
    selected_trend = request.form.get("trend_crime", trend_labels[0])
    trend_col = label_to_col[selected_trend]
    trend_df = df[["연도", "지역", trend_col]].copy()
    trend_df["발생률"] = trend_df[trend_col]

    fig_trend = px.line(
        trend_df, x="연도", y="발생률", color="지역", markers=True,
        title=f"{selected_trend} - 지역별 연도별 발생률 추이",
        labels={"발생률": "건/10만명"}, custom_data=["지역"],
        template="plotly_white"          # ✅ 명시적으로 지정
    )
    fig_trend.update_traces(
        mode="lines+markers",
        hovertemplate="연도: %{x}<br>발생률: %{y:.2f}<br>지역: %{customdata[0]}"
    )
    trend_html = fig_trend.to_html(full_html=False,  include_plotlyjs=False)

    # ─────────── 세부 범죄 설명 처리 ───────────
    raw_detail = detail_df[detail_df["사용자정의분류"] == selected_category]["C1_NM"].values[0]
    selected_details = ", ".join(re.findall(r"'([^']+)'", raw_detail)) if isinstance(raw_detail, str) else ", ".join(raw_detail)
    
    # ◆ 1) UI 선택값에 '예측 연도' 폼 항목 받아오기

    # ◆ 1) 예측 연도 + 범죄 항목만 하단에서 다시 받음 ─────
    pred_year = int(request.form.get("pred_year", 2024))
    pred_year = max(2016, min(pred_year, 2024))

    pred_target_label = request.form.get("pred_target", trend_labels[0])
    pred_target_col   = label_to_col[pred_target_label]
    # ─────────────────────────────────────────────────────

    # ◆ 2) 모델 학습/예측  (cp.train_df_ 저장)──────────────
    cp = CrimePredictor(top_n=15)
    cp.fit(df, pred_target_col, selected_region, pred_year)   # 내부에서 self.train_df_ 저장
    y_pred, err = cp.predict(df, pred_target_col, selected_region, pred_year)
    train_df   = cp.train_df_
    train_pred = cp.model.predict(train_df[cp.cols])
    # ─────────────────────────────────────────────────────

    # ◆ 3) 그래프 생성 (fig_pred 먼저 선언) ────────────────
    fig_pred = go.Figure()

    # ① 전체 실제
    hist_df = ( df.groupby("연도")[[pred_target_col]].mean().reset_index()
                if selected_region == "전국"
                else df[df["지역"] == selected_region][["연도", pred_target_col]] )
    fig_pred.add_scatter(x=hist_df["연도"], y=hist_df[pred_target_col],
                        mode="lines+markers", name="Actual")

    # ② 학습‑기간 Fitted
    fig_pred.add_scatter(x=train_df["연도"], y=train_pred,
                        mode="lines+markers", name="Fitted (Train)",
                        line=dict(dash="dot"))

    # ③ 선택 연도 예측
    fig_pred.add_scatter(x=[pred_year], y=[y_pred],
                        mode="markers", marker_symbol="diamond",
                        marker_size=12, name=f"Predicted {pred_year}")

    # ④ 선택 연도의 실제값(있으면)
    actual_row = df.query("연도 == @pred_year and 지역 == @selected_region")
    if not actual_row.empty:
        actual_val = actual_row[pred_target_col].iloc[0]
        fig_pred.add_scatter(x=[pred_year], y=[actual_val],
                            mode="markers", marker_symbol="circle-open",
                            marker_size=12, name=f"Actual {pred_year}")

    fig_pred.update_layout(
        title=f"{selected_region} – {pred_target_label} 예측",
        xaxis_title="연도", yaxis_title="건/10만명"
    )
    pred_html = fig_pred.to_html(full_html=False, include_plotlyjs=False)

    return render_template(
        "data/crime_insight.html",
        crime_categories=crime_categories,
        selected_category=selected_category,
        selected_details=selected_details,
        region_options=region_options,
        selected_region=selected_region,
        heatmap_html = heatmap_html,
        compare_trend_html=compare_trend_html,
        trend_html=trend_html,
        trend_labels=trend_labels,
        selected_trend=selected_trend,
        selected_trend1=selected_trend1,
        selected_trend2=selected_trend2,
        pred_year       = pred_year,
        pred_target     = pred_target_label,
        pred_value      = round(y_pred, 2),
        pred_error      = err,
        pred_html       = pred_html
    )


@data_bp.route("/region_corr", methods=["GET"])
def region_corr_page():
    import os, re, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
    from ..db.data_util import get_population_data

    df = get_population_data()
    df.rename(columns={"year":"연도", "region":"지역"}, inplace=True)

    meta_cols = ["연도", "지역", "population"]
    crime_cols = [c for c in df.columns if c not in meta_cols]

    for c in crime_cols:
        df[f"{c}_rate"] = df[c] / df["population"] * 1e5

    rate_cols = [c for c in df.columns if c.endswith("_rate")]

    # ---------- 선택값 ----------
    region_options  = ["전국"] + sorted(df["지역"].unique())
    selected_region = request.args.get("region", "전국")   # ← GET 으로 받는다

    # ---------- 상관계수 ----------
    if selected_region == "전국":
        region_df = df.groupby("연도")[rate_cols].mean().reset_index()
    else:
        region_df = df[df["지역"] == selected_region].copy()

    region_df = region_df.drop(columns=["연도"], errors="ignore")

    corr = region_df.corr().rename(
        columns=lambda c: c.replace("_rate","발생률"),
        index   =lambda c: c.replace("_rate","발생률")
    )

    # ---------- 캐싱된 히트맵 ----------
    safe   = re.sub(r"[^가-힣A-Za-z0-9]", "_", selected_region)
    img_fn = f"hm_{safe}.png"
    img_fp = os.path.join("static", "img", img_fn)

    if not os.path.exists(img_fp):
        sns.set(font="Malgun Gothic")           # 한글 라벨 깨짐 방지
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr, cmap="coolwarm", vmin=-1, vmax=1,
                    annot=True, fmt=".2f", square=True,
                    linewidths=.5, ax=ax)
        fig.tight_layout()
        os.makedirs(os.path.dirname(img_fp), exist_ok=True)
        fig.savefig(img_fp, dpi=150)
        plt.close(fig)



    return render_template(
        "data/region_corr.html",
        region_options = region_options,
        selected_region= selected_region,
        img_file       = img_fn
    )