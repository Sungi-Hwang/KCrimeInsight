## 📌 Project Overview & Motivation

본 프로젝트의 기획 의도는 **범죄 간의 상관관계를 분석**하여,
- 유사한 범죄군의 **공통 요인 파악**
- **환경변수 및 외부 요인**에 따른 범죄 발생률의 변화 탐색
- 장기적으로는 **지자체 및 정책 수립에 인사이트 제공**
- 그리고 **미래 범죄 발생률 예측 모델 개발**을 목표로 하였습니다.

그러나 실제 데이터 분석 과정에서 확인한 바,
- **집중 단속, 사회 정책 변화, 사건 등 외부 요인**으로 인해 **원시 데이터가 왜곡**되는 현상이 자주 발생하였고,
- 세부 범죄 레벨에서는 **법 계정이 수시로 바뀌는** 문제로 인해 일관성 있는 분석이 어렵다는 한계가 있었습니다.

따라서 본 프로젝트는 실무 활용에 있어서 다음과 같은 방향성을 갖습니다:

- 과거 **정책/사건(ex. 코로나19)** 이 특정 범죄 발생률에 어떤 영향을 미쳤는지를 분석하여,
- **미래 정책 수립에 대한 근거 기반 인사이트를 제공**하는 데 의미를 두고자 합니다.

또한, 시간이 충분하고 조직 단위의 프로젝트로 확장된다면:
- 범죄 세부 항목별 **정책, 사건, 크롤링된 외부 정보 등**을 함께 결합하여
- **더욱 정밀한 원인 분석 및 예측 모델** 개발이 가능할 것입니다.

> 단, 세부 범죄 레벨에서는 법 개정 등으로 인한 항목 변동이 잦아, **지속적인 데이터 구조 업데이트와 유지보수**가 요구됩니다.

## 📊 Results & Visualization
### 🔹 Main Page
> Flask 기반 웹 대시보드 메인 화면입니다.  
![image](https://github.com/user-attachments/assets/42006004-49bf-4f1d-b39c-5be4f688dcf2)
---

### 🔹 범죄 분류 확인 (KOSIS 기준)
> KOSIS API의 범죄 코드 체계 기반 사용자 정의 분류 구조입니다.  
 ![image](https://github.com/user-attachments/assets/f70fc0d9-dd22-4dc5-9595-9175a7fae866)
---

### 🔹 지역별 범죄 발생률 상관관계 (전국 포함)
> 각 지역 내 주요 범죄 간 상관관계를 heatmap으로 시각화한 결과입니다.  
![image](https://github.com/user-attachments/assets/2a179085-76f8-4fed-b70e-8e00c084505e)
---

### 🔹 상관관계 기반 추이 비교 (2개 범죄)
> 지역 내 두 범죄 간 상관관계가 **시계열적으로도 유사한지** 확인하기 위한 추이 그래프입니다.  
![image](https://github.com/user-attachments/assets/4a90ecec-8743-4029-8546-e379e2aac02e)
---

### 🔹 지역별 시계열 비교 (전국 범위)
> 특정 범죄의 발생 경향이 **특정 지역에 한정된 것인지** 혹은 전국적으로 유사하게 발생하는지를 파악하기 위한 시계열 비교입니다.
![image](https://github.com/user-attachments/assets/f43433c8-2aad-4013-aa7b-6bcbf45ee3b7)
---

### 🔹 예측 모델 (XGBoost Regressor)
> `objective='count:poisson'` 기반 XGBoost 회귀 모델을 활용하여 **범죄 발생률을 예측**하였습니다.  
- 예측 시 해당 지역의 **절댓값 기준 상위 5개 범죄 발생률**을 추가 feature로 사용하였습니다.
![image](https://github.com/user-attachments/assets/a8403228-d4fb-4f48-850e-a020d0629560)
---
그 외에도, 유흥업소 - 폭력범죄 상관관계, 경찰관 수, 실업률과 범죄간의 상관관계 분석을 시도하였으나,
데이터 양의 부족으로 인해 **신뢰성 있는 결과를 도출하지는 못하였습니다.**

## 📂 Folder Structure
프로젝트 전체 구조는 다음과 같습니다:

```
<Web>
projectweb/
│														
├── __init__.py      		# Flask 애플리케이션 초기화
├── __run.py                  # 디버깅용 실행파일
│
├── views/           	        < route 파일이 들어갈 폴더 >
│     ├── main_view.py          # 기본 route 설정
│     ├── auth_view.py          # 계정 관련 route 설정
│     └── data_view.py          # 데이터 페이지 route 설정
│
├── templates/       	        < HTML 템플릿 폴더 >
│     ├── base.html	        # 홈페이지 베이스 부모 HTML
│     ├── index.html	   	# 첫 화면 웹페이지 템플릿
│     ├── page_modules/	        < 공통으로 사용되는 css, js 사용 Code >
│     ├── auth/                 < 계정 관련 사용 HTML >
│     └── data/                 < 데이터 페이지 사용 HTML >
│
├── static/          		< 파일 폴더 >
│     ├── assets/               < css, js 파일 폴더>
│     ├── images/               < 이미지 폴더 >
│     └── vendor/               < 지도등 기타 css, js 폴더 > 
│
└── model/                    < DB 연동 자동화 코드 폴더 >
      └── predictor.py        
```
