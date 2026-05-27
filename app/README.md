# 부산브리핑 (BPTC Briefing) — Phase 1

부산 부동산 중개인이 사무실 PC에서 손님과 함께 보는 단지 브리핑 도구.

## 설치

```bash
cd app
pip install -r requirements.txt
```

## 비밀번호 설정 (최초 1회)

`.streamlit/secrets.toml` 파일을 열어 `APP_PASSWORD`를 원하는 값으로 변경.
(예시 파일: `.streamlit/secrets.toml.example`)

## 실행

```bash
streamlit run app.py
```

→ 브라우저가 자동으로 `http://localhost:8501`을 엽니다.

## 테스트

```bash
pytest tests/ -v
```

## 폴더 구조

```
app/
├── app.py                 # 진입점 (비밀번호 게이트 + 홈)
├── pages/                 # Streamlit 멀티페이지
│   └── 1_단지_브리핑.py
├── lib/                   # 비즈니스 로직
│   ├── db.py              # SQLite 연결
│   ├── auth.py            # 비밀번호 게이트
│   ├── queries.py         # SQL 쿼리
│   ├── charts.py          # Plotly 차트
│   └── pdf.py             # WeasyPrint PDF
├── templates/             # PDF용 HTML/CSS
├── static/fonts/          # NotoSans KR
├── tests/                 # pytest
└── .streamlit/
    ├── config.toml        # 테마
    └── secrets.toml       # 비밀번호 (gitignore)
```

## 데이터

- 공공 DB: `../02_데이터베이스/bptc_realestate.db` (읽기 전용)
- 출처: 국토교통부 실거래가 공개시스템
