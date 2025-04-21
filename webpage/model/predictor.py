# 📁 webpage/views/data_view.py

from flask import Blueprint, render_template, request, jsonify
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64, re, os
import plotly.express as px
import plotly.io as pio

from webpage.db import data_util, ent_util

# ────────────────────────────────────────────────────────
data_bp = Blueprint("data", __name__, url_prefix="/data")

# 🔧 공통 전처리 함수 (분리된 함수로 유지)
def preprocess_crime_rate(df):
    df = df.copy()
    df.rename(columns={"year": "연도", "region": "지역"}, inplace=True)
    meta_cols = ["연도", "지역", "population"]
    crime_cols = [c for c in df.columns if c not in meta_cols]
    for c in crime_cols:
        df[f"{c}_rate"] = df[c] / df["population"] * 1e3
    rate_cols = [c for c in df.columns if c.endswith("_rate")]
    return df, rate_cols

# 🎯 분석 페이지 (예측 기능 없이 시각화 중심)
@data_bp.route("/insight", methods=["GET", "POST"])
def crime_insight_page():
    import matplotlib
    matplotlib.use('Agg')  # 웹 서버에서 렌더링용 백엔드 사용
    matplotlib.rc('font', family='Malgun Gothic')
    matplotlib.rcParams['axes.unicode_minus'] = False

    df = data_util.get_population_data()
    df, rate_cols = preprocess_crime_rate(df)
    detail_df = data_util.get_crsis_code_data()

    crime_categories = detail_df["사용자정의분류"].tolist()
    selected_category = request.form.get("category", crime_categories[0])

    region_options = ["전국"] + sorted(df["지역"].unique())
    selected_region = request.form.get("region", "전국")

    region_df = df.groupby("연도")[rate_cols].mean() if selected_region == "전국" else df[df["지역"] == selected_region][rate_cols]
    region_df = region_df.drop(columns=["연도"], errors="ignore")
    corr = region_df.corr()

    labels = [col.replace("_rate", " 발생률") for col in corr.columns]
    corr.columns = labels
    corr.index = labels

    # 히트맵 HTML 내 표시를 위한 base64 이미지 생성
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, cmap="coolwarm", vmin=-1, vmax=1,
                annot=True, fmt=".2f", square=True, linewidths=.5, ax=ax)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    heatmap_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # 라벨 매핑 처리
    rate_label_map = {col: col.replace("_rate", " 발생률") for col in rate_cols}
    label_to_col = {v: k for k, v in rate_label_map.items()}
    trend_labels = list(label_to_col.keys())

    selected_trend1 = request.form.get("trend_crime1", trend_labels[0])
    selected_trend2 = request.form.get("trend_crime2", trend_labels[1] if len(trend_labels) > 1 else trend_labels[0])

    trend_col1 = label_to_col[selected_trend1]
    trend_col2 = label_to_col[selected_trend2]
    line_df = df.groupby("연도")[[trend_col1, trend_col2]].mean().reset_index() if selected_region == "전국" else df[df["지역"] == selected_region][["연도", trend_col1, trend_col2]]

    # 이중 Y축 그래프 (matplotlib)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    color1 = "tab:blue"
    color2 = "tab:red"

    ax1.set_xlabel("연도")
    ax1.set_ylabel(selected_trend1, color=color1)
    ax1.plot(line_df["연도"], line_df[trend_col1], color=color1, marker='o')
    ax1.tick_params(axis='y', labelcolor=color1)

    ax2 = ax1.twinx()
    ax2.set_ylabel(selected_trend2, color=color2)
    ax2.plot(line_df["연도"], line_df[trend_col2], color=color2, linestyle='--', marker='o')
    ax2.tick_params(axis='y', labelcolor=color2)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    compare_trend_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # detail 처리
    raw_detail = detail_df[detail_df["사용자정의분류"] == selected_category]["C1_NM"].values[0]
    selected_details = ", ".join(re.findall(r"'([^']+)'", raw_detail)) if isinstance(raw_detail, str) else ", ".join(raw_detail)

    # 단일 추이 그래프 (Plotly 그대로 유지)
    selected_trend = request.form.get("trend_crime", trend_labels[0])
    trend_col = label_to_col[selected_trend]
    trend_df = df[["연도", "지역", trend_col]].copy()
    trend_df["발생률"] = trend_df[trend_col]

    fig = px.line(trend_df, x="연도", y="발생률", color="지역", markers=True,
                  title=f"{selected_trend} - 지역별 연도별 발생률 추이",
                  labels={"발생률": "건/10만명"}, custom_data=["지역"])
    fig.update_traces(mode="lines+markers", hovertemplate="연도: %{x}<br>발생률: %{y:.2f}<br>지역: %{customdata[0]}")
    trend_bytes = pio.to_image(fig, format="png", width=900, height=500, scale=2)
    trend_b64 = base64.b64encode(trend_bytes).decode("utf-8")

    return render_template(
        "data/crime_insight.html",
        crime_categories=crime_categories,
        selected_category=selected_category,
        selected_details=selected_details,
        region_options=region_options,
        selected_region=selected_region,
        heatmap_b64=heatmap_b64,
        trend_b64=trend_b64,
        trend_labels=trend_labels,
        selected_trend=selected_trend,
        compare_trend_b64=compare_trend_b64,
        selected_trend1=selected_trend1,
        selected_trend2=selected_trend2,
    )
