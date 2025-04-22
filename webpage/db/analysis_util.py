import pandas as pd
import pymysql
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from scipy.stats import pearsonr, spearmanr, linregress

def get_correlation_data(selected_type='전체'):
    conn = pymysql.connect(
        host='192.168.0.234',
        user='teamuser',
        password='team1234',
        db='1team_database',
        charset='utf8mb4'
    )
    region_map = {
        '서울특별시': '서울',
        '부산광역시': '부산',
        '대구광역시': '대구',
        '인천광역시': '인천',
        '광주광역시': '광주',
        '대전광역시': '대전',
        '울산광역시': '울산',
        '세종특별자치시': '세종',
        '경기도': '경기',
        '강원특별자치도': '강원',
        '충청북도': '충북',
        '충청남도': '충남',
        '전라북도': '전북',
        '전북특별자치도': '전북',
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주'
    }

    if selected_type == '전체':
        sql = """
            SELECT 시도 AS 지역, SUM(`간이주점` + `기타` + `노래클럽` + `룸살롱` + `비어_바_살롱` + `카바레`) AS 엔터수
            FROM entertain_bar 
            GROUP BY 시도
        """
    else:
        sql = f"""
            SELECT 시도 AS 지역, SUM(`{selected_type}`) AS 엔터수 
            FROM entertain_bar 
            GROUP BY 시도"""

    ent_df = pd.read_sql(sql, conn)
    ent_df['지역'] = ent_df['지역'].map(region_map)

    crime_df = pd.read_sql("""
        SELECT 지역, SUM(폭력범죄) AS 폭력범죄건수
        FROM crime_data_2011_2022_edit
        WHERE 연도=2022 
        GROUP BY 지역
    """, conn)

    merged_df = pd.merge(ent_df, crime_df, on='지역')

    if len(merged_df) < 2:
        conn.close()
        return None, 0, 0, 0, 0, [], []

    pearson_corr, pearson_p = pearsonr(merged_df['엔터수'], merged_df['폭력범죄건수'])
    spearman_corr, spearman_p = spearmanr(merged_df['엔터수'], merged_df['폭력범죄건수'])
    regression = linregress(merged_df['엔터수'], merged_df['폭력범죄건수'])

    regression_line = [{"x": x, "y": regression.slope * x + regression.intercept} for x in merged_df['엔터수']]
    scatter_data = [{"x": row['엔터수'], "y": row['폭력범죄건수']} for _, row in merged_df.iterrows()]

    conn.close()

    return (merged_df, 
            round(pearson_corr, 3), round(pearson_p, 4),
            round(spearman_corr, 3), round(spearman_p, 4),
            scatter_data, regression_line)

def get_correlation_ratio_data(selected_type='전체'):
    conn = pymysql.connect(
        host='192.168.0.234',
        user='teamuser',
        password='team1234',
        db='1team_database',
        charset='utf8mb4'
    )
    region_map = {
        '서울특별시': '서울',
        '부산광역시': '부산',
        '대구광역시': '대구',
        '인천광역시': '인천',
        '광주광역시': '광주',
        '대전광역시': '대전',
        '울산광역시': '울산',
        '세종특별자치시': '세종',
        '경기도': '경기',
        '강원특별자치도': '강원',
        '충청북도': '충북',
        '충청남도': '충남',
        '전라북도': '전북',
        '전북특별자치도': '전북',
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주'
    }

    # 유흥업소 데이터
    if selected_type == '전체':
        sql = """
            SELECT 시도 AS 지역, SUM(`간이주점` + `기타` + `노래클럽` + `룸살롱` + `비어_바_살롱` + `카바레`) AS 엔터수
            FROM entertain_bar 
            GROUP BY 시도
        """
    else:
        sql = f"""
            SELECT 시도 AS 지역, SUM(`{selected_type}`) AS 엔터수 
            FROM entertain_bar 
            GROUP BY 시도
            """

    ent_df = pd.read_sql(sql, conn)
    ent_df['지역'] = ent_df['지역'].map(region_map)

    # 범죄 데이터
    crime_df = pd.read_sql("""
        SELECT 지역, SUM(폭력범죄) AS 폭력범죄건수
        FROM crime_data_2011_2022_edit
        WHERE 연도=2022 GROUP BY 지역
    """, conn)

    # 인구 데이터
    pop_df = pd.read_sql("""
        SELECT region AS 지역, `2022_15세이상인구__천명_` AS 인구수
        FROM merged_data_jh
    """, conn)


    # 병합
    merged_df = pd.merge(ent_df, crime_df, on='지역')
    merged_df = pd.merge(merged_df, pop_df, on='지역')

    if len(merged_df) < 2:
        conn.close()
        return None, 0, 0, 0, 0, [], []

    # 비율 계산
    merged_df['업소수비율'] = merged_df['엔터수'] / merged_df['인구수']
    merged_df['범죄건수비율'] = merged_df['폭력범죄건수'] / merged_df['인구수']

    # 상관계수 계산
    pearson_corr, pearson_p = pearsonr(merged_df['업소수비율'], merged_df['범죄건수비율'])
    spearman_corr, spearman_p = spearmanr(merged_df['업소수비율'], merged_df['범죄건수비율'])

    regression = linregress(merged_df['업소수비율'], merged_df['범죄건수비율'])
    regression_line = [{"x": x, "y": regression.slope * x + regression.intercept} for x in merged_df['업소수비율']]
    scatter_data = [{"x": row['업소수비율'], "y": row['범죄건수비율']} for _, row in merged_df.iterrows()]

    conn.close()
    return (merged_df, round(pearson_corr, 3), round(pearson_p, 4),
            round(spearman_corr, 3), round(spearman_p, 4),
            scatter_data, regression_line)

def get_density_correlation_data(selected_type='전체',  ent_basis='area', crime_basis='area', remove_outliers=False):
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4'
        )
        
        # 엔터 업소 데이터
        ent_sql = """
            SELECT 시도, 시군구, 
                (간이주점 + 기타 + 노래클럽 + 룸살롱 + 비어_바_살롱 + 카바레) AS 엔터수
            FROM entertain_bar
        """
        ent_df = pd.read_sql(ent_sql, conn)

        # 범죄 데이터 (폭력범죄만)
        crime_sql = """
            SELECT 시도, 시군구, SUM(발생건수) AS 폭력범죄건수
            FROM crime_area_2023
            WHERE 범죄대분류 = '폭력범죄'
            GROUP BY 시도, 시군구
        """
        crime_df = pd.read_sql(crime_sql, conn)

        # 면적 데이터
        area_sql = """
            SELECT 자치구명, `면적(km²)` AS 면적
            FROM origin_ground_area
        """
        area_df = pd.read_sql(area_sql, conn)
        # 시도, 시군구 분리
        area_df[['시도', '시군구']] = area_df['자치구명'].str.split(' ', n=1, expand=True)


        # 인구 데이터
        pop_sql = """
            SELECT 시도명 AS 시도, 시군구명 AS 시군구, SUM(계) AS 인구수
            FROM origin_population_age
            GROUP BY 시도명, 시군구명
        """
        pop_df = pd.read_sql(pop_sql, conn)


        # 병합
        merged_df = pd.merge(ent_df, crime_df, on=['시도', '시군구'], how='inner')
        merged_df = pd.merge(merged_df, area_df[['시도', '시군구', '면적']], on=['시도', '시군구'], how='inner')
        merged_df = pd.merge(merged_df, pop_df[['시도', '시군구', '인구수']], on=['시도', '시군구'], how='inner')
        
        # 밀집도 계산
        if ent_basis == 'area':
            merged_df['업소밀집도'] = merged_df['엔터수'] / merged_df['면적']
        else:
            merged_df['업소밀집도'] = merged_df['엔터수'] / merged_df['인구수']

        if crime_basis == 'area':
            merged_df['폭력범죄밀집도'] = merged_df['폭력범죄건수'] / merged_df['면적']
        else:
            merged_df['폭력범죄밀집도'] = merged_df['폭력범죄건수'] / merged_df['인구수']
        if len(merged_df) < 2:
            return None, 0, 0, 0, 0, [], [], 0, 0
        
        merged_df['자치구명'] = merged_df['시도'] + ' ' + merged_df['시군구']
        
        scatter_data = [
            {"x": row["업소밀집도"], "y": row["폭력범죄밀집도"], "title": row["자치구명"]}
            for _, row in merged_df.iterrows()
        ]

        # 🔥 아웃라이어 제거 (선택)
        if remove_outliers:
            Q1_x = merged_df['업소밀집도'].quantile(0.25)
            Q3_x = merged_df['업소밀집도'].quantile(0.75)
            IQR_x = Q3_x - Q1_x

            Q1_y = merged_df['폭력범죄밀집도'].quantile(0.25)
            Q3_y = merged_df['폭력범죄밀집도'].quantile(0.75)
            IQR_y = Q3_y - Q1_y

            merged_df = merged_df[
                (merged_df['업소밀집도'] >= Q1_x - 1.5 * IQR_x) & (merged_df['업소밀집도'] <= Q3_x + 1.5 * IQR_x) &
                (merged_df['폭력범죄밀집도'] >= Q1_y - 1.5 * IQR_y) & (merged_df['폭력범죄밀집도'] <= Q3_y + 1.5 * IQR_y)
            ]


        # 상관계수 계산
        pearson_corr, pearson_p = pearsonr(merged_df['업소밀집도'], merged_df['폭력범죄밀집도'])
        spearman_corr, spearman_p = spearmanr(merged_df['업소밀집도'], merged_df['폭력범죄밀집도'])

        # 회귀선 계산
        regression = linregress(merged_df['업소밀집도'], merged_df['폭력범죄밀집도'])
        regression_line = [{"x": x, "y": regression.slope * x + regression.intercept} for x in merged_df['업소밀집도']]

        # 산점도 데이터
        scatter_data = [{"x": row['업소밀집도'], "y": row['폭력범죄밀집도']} for _, row in merged_df.iterrows()]

        # 최대값
        max_x = merged_df['업소밀집도'].max() * 1.1
        max_y = merged_df['폭력범죄밀집도'].max() * 1.1

        return merged_df.to_dict(orient='records'), round(pearson_corr, 3), round(pearson_p, 4), round(spearman_corr, 3), round(spearman_p, 4), scatter_data, regression_line, max_x, max_y

    except Exception as e:
        print("밀집도 상관분석 실패 : ", e)
        return None, 0, 0, 0, 0, [], [], 0, 0

    finally:
        if conn:
            conn.close()