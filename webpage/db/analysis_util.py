import pandas as pd
import pymysql
from scipy.stats import spearmanr, pearsonr

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
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주'
    }

    if selected_type == '전체':
        sql = """
            SELECT 시도 as 지역, 
                   SUM(`간이주점` + `기타` + `노래클럽` + `룸살롱` + `비어_바_살롱` + `카바레`) as 엔터수
            FROM entertain_bar
            GROUP BY 시도
        """
    else:
        sql = f"""
            SELECT 시도 as 지역, SUM(`{selected_type}`) as 엔터수
            FROM entertain_bar
            GROUP BY 시도
        """

    ent_df = pd.read_sql(sql, conn)
    ent_df['지역'] = ent_df['지역'].map(region_map)
    ent_df = ent_df.groupby('지역', as_index=False).sum()

    crime_df = pd.read_sql("""
        SELECT 지역, SUM(폭력범죄) as 폭력범죄건수
        FROM crime_data_2011_2022_edit
        WHERE 연도 = 2022
        GROUP BY 지역
    """, conn)
    crime_df = crime_df.groupby('지역', as_index=False).sum()

    merged_df = pd.merge(ent_df, crime_df, on='지역')

    pearson_corr, pearson_p = pearsonr(merged_df['엔터수'], merged_df['폭력범죄건수'])
    spearman_corr, spearman_p = spearmanr(merged_df['엔터수'], merged_df['폭력범죄건수'])

    scatter_data = [{"x": row['엔터수'], "y": row['폭력범죄건수']} for _, row in merged_df.iterrows()]

    conn.close()

    return (merged_df, 
            round(pearson_corr, 3), round(pearson_p, 4),
            round(spearman_corr, 3), round(spearman_p, 4),
            scatter_data)


def get_filtered_correlation_data():
    conn = pymysql.connect(
        host='192.168.0.234',
        user='teamuser',
        password='team1234',
        db='1team_database',
        charset='utf8mb4'
    )

    # 시도명 → 2글자 약칭 매핑
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
        '전라남도': '전남',
        '경상북도': '경북',
        '경상남도': '경남',
        '제주특별자치도': '제주'
    }

    # 엔터테인먼트 데이터 (특정 업종만 합계)
    ent_df = pd.read_sql("""
        SELECT 시도 as 지역, 
               SUM(`간이주점` + `기타` + `노래클럽` + `룸살롱` + `비어_바_살롱` + `카바레`) as 엔터수
        FROM entertain_bar
        GROUP BY 시도
    """, conn)

    ent_df['지역'] = ent_df['지역'].map(region_map)
    ent_df = ent_df.groupby('지역', as_index=False).sum()

    # 범죄 데이터
    crime_df = pd.read_sql("""
        SELECT 지역, SUM(폭력범죄) as 폭력범죄건수
        FROM crime_data_2011_2022_edit
        WHERE 연도 = 2022
        GROUP BY 지역
    """, conn)
    crime_df = crime_df.groupby('지역', as_index=False).sum()

    # 병합
    merged_df = pd.merge(ent_df, crime_df, on='지역')

    # 상관계수 & p-value 계산
    pearson_corr, pearson_p = pearsonr(merged_df['엔터수'], merged_df['폭력범죄건수'])
    spearman_corr, spearman_p = spearmanr(merged_df['엔터수'], merged_df['폭력범죄건수'])

    # 산점도 데이터
    scatter_data = [{"x": row['엔터수'], "y": row['폭력범죄건수']} for _, row in merged_df.iterrows()]

    conn.close()

    return (merged_df, 
            round(pearson_corr, 3), round(pearson_p, 4),
            round(spearman_corr, 3), round(spearman_p, 4),
            scatter_data)


def get_correlation_ratio_data(selected_type='전체'):
    conn = pymysql.connect(
        host='192.168.0.234',
        user='teamuser',
        password='team1234',
        db='1team_database',
        charset='utf8mb4'
    )

    region_map = {
        '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
        '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
        '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
        '강원특별자치도': '강원', '충청북도': '충북', '충청남도': '충남',
        '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
        '경상남도': '경남', '제주특별자치도': '제주'
    }

    # 엔터테인먼트 데이터
    if selected_type == '전체':
        sql = """
            SELECT 시도 as 지역, 
                   SUM(`간이주점` + `기타` + `노래클럽` + `룸살롱` + `비어_바_살롱` + `카바레`) as 엔터수
            FROM entertain_bar
            GROUP BY 시도
        """
    else:
        sql = f"""
            SELECT 시도 as 지역, SUM(`{selected_type}`) as 엔터수
            FROM entertain_bar
            GROUP BY 시도
        """
    ent_df = pd.read_sql(sql, conn)
    ent_df['지역'] = ent_df['지역'].map(region_map)
    ent_df = ent_df.groupby('지역', as_index=False).sum()

    # 범죄 데이터
    crime_df = pd.read_sql("""
        SELECT 지역, SUM(폭력범죄) as 폭력범죄건수
        FROM crime_data_2011_2022_edit
        WHERE 연도 = 2022
        GROUP BY 지역
    """, conn)
    crime_df = crime_df.groupby('지역', as_index=False).sum()

    # 엔터 + 범죄 병합
    merged_df = pd.merge(ent_df, crime_df, on='지역')

    # 인구수 데이터
    pop_df = pd.read_sql("""
        SELECT region as 지역, `2022_15세이상인구__천명_` as 인구수
        FROM merged_data_jh
    """, conn)

    # 병합 (왼쪽 병합: 엔터+범죄 데이터에 인구수 붙이기)
    merged_df = pd.merge(merged_df, pop_df, on='지역', how='left')

    # 비율 계산
    merged_df['업소수비율'] = merged_df['엔터수'] / merged_df['인구수']
    merged_df['범죄건수비율'] = merged_df['폭력범죄건수'] / merged_df['인구수']

    # 상관계수 계산
    pearson_corr, pearson_p = pearsonr(merged_df['업소수비율'], merged_df['범죄건수비율'])
    spearman_corr, spearman_p = spearmanr(merged_df['업소수비율'], merged_df['범죄건수비율'])

    conn.close()

    return (merged_df, 
            round(pearson_corr, 3), round(pearson_p, 4),
            round(spearman_corr, 3), round(spearman_p, 4),
            [])

