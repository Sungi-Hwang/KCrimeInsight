import pymysql

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

def select_crime_data_23(offset=0, limit=20):
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
        sql = f"SELECT * FROM crime_area_2023 LIMIT {limit} OFFSET {offset}"
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


def count_crime_data_23():
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
        cursor.execute("SELECT COUNT(*) FROM crime_area_2023")
        count = cursor.fetchone()[0]

    except Exception as e:
        print("카운트 가져오기 실패:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return count


def get_crime_data_23_columns():
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
        cursor.execute("SELECT * FROM crime_area_2023 LIMIT 1")
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
