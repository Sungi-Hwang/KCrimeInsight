import pymysql
import pandas as pd
import sqlite3
from sqlalchemy import create_engine


def select_crime_data_11_22(offset=0, limit=20):
    rows = []
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        sql = f"SELECT * FROM crime_data_2011_2022_edit LIMIT {limit} OFFSET {offset}"
        cursor.execute(sql)
        rows = cursor.fetchall()

    except Exception as e:
        print("데이터 불러오기 실패 : ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return rows


def count_crime_data_11_22():
    count = 0
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM crime_data_2011_2022_edit")
        count = cursor.fetchone()[0]

    except Exception as e:
        print("카운트 가져오기 실패:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return count


def get_crime_data_11_22_columns():
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crime_data_2011_2022_edit LIMIT 1")
        column_names = [desc[0] for desc in cursor.description]
        return column_names

    except Exception as e:
        print("칼럼 이름 가져오기 실패:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def chart_crime(selected_year='전체', selected_crime='전체'):
    try:
        crime_columns = ["강도", "교통범죄", "노동범죄", "도박범죄", "마약범죄", "병역범죄",
                     "보건범죄", "살인기수", "살인미수등", "선거범죄", "성풍속범죄", "안보범죄",
                     "절도범죄", "지능범죄", "특별경제범죄", "폭력범죄", "환경범죄"]

        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()

        query = "SELECT * FROM crime_data_2011_2022_edit"
        cursor.execute(query)
        rows2 = cursor.fetchall()

    except Exception as e:
        print("데이터 불러오기 실패 : ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return rows2


def chart_crime_ratio(selected_year, selected_crime):
    engine = create_engine("mysql+pymysql://teamuser:team1234@192.168.0.234:3306/1team_database")

    crime_df = pd.read_sql("SELECT * FROM crime_data_2011_2022_edit", engine)
    pop_df = pd.read_sql("SELECT region as 지역, `2022_15세이상인구__천명_` as 인구수 FROM merged_data_jh", engine)

    crime_columns = ["강도", "교통범죄", "노동범죄", "도박범죄", "마약범죄", "병역범죄",
                     "보건범죄", "살인기수", "살인미수등", "선거범죄", "성풍속범죄", "안보범죄",
                     "절도범죄", "지능범죄", "특별경제범죄", "폭력범죄", "환경범죄"]

    for col in crime_columns:
        crime_df[col] = pd.to_numeric(crime_df[col], errors='coerce')

    if selected_year != '전체':
        # 선택 연도만 필터
        crime_df = crime_df[crime_df['연도'] == int(selected_year)]
        crime_df = crime_df.groupby(['지역'])[crime_columns].sum().reset_index()
    else:
        # 전체 연도면 연도 빼고 지역만 그룹화
        crime_df = crime_df.groupby(['지역'])[crime_columns].sum().reset_index()

    # 인구수 병합
    crime_df = pd.merge(crime_df, pop_df, on='지역', how='left')

    crime_df['인구수'] = pd.to_numeric(crime_df['인구수'], errors='coerce')
    crime_df = crime_df[crime_df['인구수'].notnull()]

    # 비율 계산
    for col in crime_columns:
        crime_df[f"{col}비율"] = crime_df[col] / crime_df['인구수']

    return crime_df


def get_all_regions():
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT 지역 FROM crime_data_2011_2022_edit")
            rows = cursor.fetchall()
            return [row['지역'] for row in rows]
    except Exception as e:
        print("지역 목록 불러오기 실패:", e)
        return []
    finally:
        conn.close()



def get_crime_data_for_region(region, year='2022'):
    # DB 연결
    conn = pymysql.connect(
        host='192.168.0.234',
        port=3306,
        user='teamuser',
        password='team1234',
        database='1team_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            # 연도와 지역에 맞는 범죄 데이터를 가져오기
            sql = f"""
                SELECT 강도, 교통범죄, 노동범죄, 도박범죄, 마약범죄, 
                       병역범죄, 보건범죄, 살인기수, 살인미수등, 
                       선거범죄, 성풍속범죄, 안보범죄, 절도범죄, 
                       지능범죄, 특별경제범죄, 폭력범죄, 환경범죄
                FROM crime_data_2011_2022_edit
                WHERE 지역 = %s AND 연도 = %s
            """
            cursor.execute(sql, (region, year))
            result = cursor.fetchone()

            if result:
                return result  # 딕셔너리 형태로 리턴됨
            else:
                return {}  # 데이터 없음

    finally:
        conn.close()