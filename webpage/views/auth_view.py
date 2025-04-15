from flask import Blueprint
from flask import render_template, redirect, url_for 
from flask import request, session
from dotenv import load_dotenv

from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

from ..db import member_util

import os
import random, string
import smtplib

load_dotenv()

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def send_email(email, username, temp_pw):
    MAIL_USER = os.getenv('MAIL_USER')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    msg = MIMEText(f"""{username}님, 요청하신 임시 비밀번호는 다음과 같습니다:

임시 비밀번호: {temp_pw}

로그인 후 반드시 비밀번호를 변경해 주세요.""")
    msg['Subject'] = "임시 비밀번호 안내"
    msg['From'] = MAIL_USER
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(MAIL_USER, MAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("메일 발송 실패:", e)
        return False
    return True

@auth_bp.route("/login/", methods=['GET','POST'])
def login():
    if request.method.lower() == 'get':
        return render_template("auth/page-login.html")
    else:
        # 1. 요청 데이터 읽기
        email = request.form.get('email','')
        passwd = request.form.get('passwd','')
        remember = request.form.get('remember','')

        # 2. 요청 처리
        row = member_util.select_member_by_email(email)
        print(row)
        if not row: # 조회된 row가 없다면
            return render_template("auth/page-login.html", message="존재하지 않는 이메일입니다.")    # 템플릿(.html)에 전달되는 데이터

        if check_password_hash(row[1], passwd):
            session['loginuser'] = email                    # 로그인 처리 : 세션에 로그인 관련 데이터 저장 
            return redirect(url_for('main.index'))          # main blueprint의 index 함수에 연결된 경로로 이동
        else:   # 로그인 실패

            # 3. 응답 컨텐츠 만들기
            return render_template("auth/page-login.html")  # 주소와 일치하는 화면을 보여줄때
            # return redirect(url_for('auth.login'))        # 새로고침할때 오류가 발생하기에 이 사용이 좋음

@auth_bp.route("/logout/", methods=['GET'])
def logout():
    #del session['loginuser']           # session의 개별 데이터 제거
    # session.pop('loginuser', None)    # session의 개별 데이터 제거
    #session['loginuser'] == None       # session의 개별 데이터 제거
    session.clear()                     # session의 모든 데이터 제거
    return redirect(url_for('main.index'))


@auth_bp.route("/register/", methods=['GET','POST'])
def register():
    if request.method.lower() == 'get':
        return render_template('auth/page-register.html')
    else:
        username = request.form.get('username')
        email = request.form.get('email')
        passwd = request.form.get('passwd')

        # 이메일 중복 체크
        existing_user = member_util.select_member_by_email(email)
        if existing_user:
            return render_template('auth/page-register.html', message="이미 사용 중인 이메일입니다.")

        passwd_hash = generate_password_hash(passwd)
        member_util.insert_member(email, passwd_hash, username)
        return redirect(url_for('auth.login'))
    
@auth_bp.route("/forget/", methods=['GET', 'POST'])
def forget_password():
    if request.method.lower() == 'get':
        return render_template("auth/pages-forget.html")
    
    # 1. 입력값 받기
    email = request.form.get('email','')
    username = request.form.get('username','')

    row = member_util.select_member_by_email(email)
    if not row or len(row) < 3:
        return render_template("auth/pages-forget.html", message="존재하지 않는 이메일입니다.")

    db_username = row[2]
    if username.strip().lower() != db_username.strip().lower():
        return render_template("auth/pages-forget.html", message="이메일과 이름이 일치하지 않습니다.")

    # 2. 임시 비밀번호 생성 및 해시
    temp_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    passwd_hash = generate_password_hash(temp_pw)

    # 3. DB 비밀번호 업데이트
    member_util.update_password_by_email(email, passwd_hash)

    # 4. 이메일 발송
    if send_email(email, username, temp_pw):
        return render_template("auth/pages-forget.html", message="임시 비밀번호를 이메일로 보냈습니다.")
    else:
        return render_template("auth/pages-forget.html", message="메일 발송에 실패했습니다. 관리자에게 문의하세요.")