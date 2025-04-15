import pymysql

def insert_member(email, passwd, username):
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4')
        cursor = conn.cursor()

        sql = "insert into member (email, passwd, username) values (%s, %s, %s)"
        cursor.execute(sql, (email, passwd, username))
        conn.commit()
        pass
    except Exception as e:
        print("데이터 저장 실패 : ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def select_member_by_email(email):
    row = None
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4')
        cursor = conn.cursor()

        sql = """select email, passwd, username, usertype, regdate 
                from member 
                where email = %s and deleted = FALSE"""
        
        cursor.execute(sql, (email, ))
        row = cursor.fetchone()
    except Exception as e:
        print("로그인 실패 : ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return row    

def update_password_by_email(email, passwd_hash):
    try:
        conn = pymysql.connect(
            host='192.168.0.234',
            port=3306,
            user='teamuser',
            password='team1234',
            database='1team_database',
            charset='utf8mb4')
        cursor = conn.cursor()

        sql = "UPDATE member SET passwd = %s WHERE email = %s AND deleted = FALSE"
        cursor.execute(sql, (passwd_hash, email))
        conn.commit()
    except Exception as e:
        print("비밀번호 변경 실패: ", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
