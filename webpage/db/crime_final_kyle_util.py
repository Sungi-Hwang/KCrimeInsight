import pymysql

def select_crime_kyle_data(offset=0, limit=20):
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
        sql = f"SELECT * FROM crime_final_kyle LIMIT {limit} OFFSET {offset}"
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


def count_crime_kyle_data():
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
        cursor.execute("SELECT COUNT(*) FROM scrime_final_kyle")
        count = cursor.fetchone()[0]

    except Exception as e:
        print("카운트 가져오기 실패:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return count


def get_crime_kyle_columns():
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
        cursor.execute("SELECT * FROM crime_final_kyle LIMIT 1")
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

def crimes_data(selected_crimes='전체'):
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
        cursor = conn.cursor()

        query = "SELECT * FROM crime_final_kyle"
        cursor.execute(query)
        rows_crimes = cursor.fetchall()

    except Exception as e:
        print("데이터 불러오기 실패 : ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return rows_crimes