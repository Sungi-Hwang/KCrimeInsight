```
<Web>
projectweb/
│														
├── __init__.py      		# Flask 애플리케이션 초기화
├── views/           	        < route 파일이 들어갈 폴더 >
│     └── main_view.py          # 기본 route 설정
├── templates/       	        < HTML 템플릿 폴더 >
│     ├── page_modules/	        < 공통으로 사용되는 css, js 사용 Code >
│     ├── base.html	        # 홈페이지 베이스 부모 HTML
│     └── index.html	   	# 첫 화면 웹페이지 템플릿
└── static/          		< css, js 파일 폴더 >
      ├── css/
      ├── js/
      ├── images/
      └── vendor/
```
