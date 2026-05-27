# 부산브리핑 — 프로젝트 스펙

> AI가 코드를 짤 때 지켜야 할 규칙과 절대 하면 안 되는 것.
> 이 문서를 AI에게 항상 함께 공유하세요.

---

## 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | Streamlit 1.40+ | 파이썬으로 데이터 웹앱 한 줄 작성. SQLite·Pandas와 궁합 최상. 1인 사무실 도구에 최적 |
| DB (공공) | SQLite (`bptc_realestate.db`) | 이미 준비된 파일. 외부 서버 불필요 |
| DB (사용자) | SQLite (`briefing_app.db` 분리) | 공공데이터 갱신 시 충돌 방지. ATTACH로 결합 조회 |
| 데이터 처리 | Pandas 2.x | DB → DataFrame → 차트 흐름 표준 |
| 차트 | Plotly | 인터랙티브 + PDF 정적 변환 모두 가능 |
| 지도 | Folium (Phase 3 옵션) | gu_centers 좌표 그대로 사용 |
| PDF | WeasyPrint | HTML/CSS 그대로 A4 PDF. 한글 폰트 지원 |
| 인증 | Streamlit secrets + session_state | 공용 비밀번호 1개. 외부 OAuth 불필요 |
| 배포 | 로컬 PC 실행 (`streamlit run app.py`) | 사무실 PC 단독 사용. 클라우드 비용 0 |
| 패키지 관리 | uv (또는 pip) | requirements.txt 단일 파일 |

---

## 프로젝트 구조

```
bptc-data-pack-main/
├── 02_데이터베이스/
│   └── bptc_realestate.db        # 공공데이터 (읽기 전용, 절대 수정 X)
├── PRD/                          # 본 문서 폴더
├── app/                          # ← 새로 만들 작업 폴더
│   ├── app.py                    # Streamlit 엔트리 (멀티페이지)
│   ├── pages/
│   │   ├── 1_단지_브리핑.py      # Phase 1
│   │   ├── 2_손님_관리.py        # Phase 2
│   │   ├── 3_단지_비교.py        # Phase 2
│   │   ├── 4_매물_매칭.py        # Phase 2
│   │   └── 5_일일_리포트.py      # Phase 3
│   ├── lib/
│   │   ├── db.py                 # SQLite 연결 + ATTACH
│   │   ├── queries.py            # SQL 모음 (apt_trade/rent/complex…)
│   │   ├── charts.py             # Plotly 차트 팩토리
│   │   ├── pdf.py                # HTML → PDF 렌더링
│   │   ├── matching.py           # Phase 2 매칭 점수 알고리즘
│   │   └── auth.py               # 비밀번호 게이트
│   ├── templates/
│   │   ├── briefing.html         # PDF용 HTML 템플릿
│   │   └── styles.css            # A4 인쇄 스타일
│   ├── briefing_app.db           # 사용자 데이터 (Phase 2부터)
│   ├── pdfs/                     # 생성된 PDF 보관
│   ├── .streamlit/
│   │   ├── config.toml           # 테마/페이지 설정
│   │   └── secrets.toml          # APP_PASSWORD (gitignore)
│   ├── requirements.txt
│   └── README.md                 # 실행 방법
```

---

## 절대 하지 마 (DO NOT)

> AI에게 코드를 시킬 때 이 목록을 반드시 함께 공유하세요.

- [ ] `bptc_realestate.db`의 스키마 변경 / 데이터 INSERT·UPDATE·DELETE 절대 금지 — 공공데이터는 매월 통째 재생성됨
- [ ] 단지명·자치구명을 코드에 하드코딩 ("해운대구" 같은 리스트). 항상 `gu_codes_realty`에서 SELECT
- [ ] 거래금액(dealAmount)을 "원" 단위로 가정 — **만원 단위**임 (498000 = 49.8억)
- [ ] 비밀번호를 .py 파일에 직접 적기. 반드시 `st.secrets["APP_PASSWORD"]`
- [ ] Phase 1에서 사용자 데이터 테이블 생성. customer/briefing은 Phase 2부터
- [ ] PDF 생성을 동기로 처리한 후 30초 넘게 페이지 멈추기 — `st.spinner` + 비동기 권장
- [ ] Phase 3 공유 페이지에 `broker_memo` 노출 — 영업 내부 메모는 외부 절대 금지
- [ ] 매칭 점수 가중치를 코드에 하드코딩. `config.toml`로 분리해 튜닝 가능하게
- [ ] 차트 색상에 빨강·녹색만 쓰기 (색맹 배려). 회색 + 네이비 + 포인트 1색 권장
- [ ] 학교·학원 정보를 "이 단지 전용"이라고 라벨링 — 실제는 **자치구 단위** 집계
- [ ] 이상거래 탐지 결과에 단정적 표현 ("거품임", "비정상"). "참고용", "추가 검토 필요"로 완곡하게
- [ ] DB 쿼리에 사용자 입력 문자열 직접 삽입 (SQL injection). 항상 파라미터 바인딩

---

## 항상 해 (ALWAYS DO)

- [ ] 변경 전에 계획을 먼저 보여줘 (어떤 파일을 만들지/수정할지)
- [ ] 비밀번호·API 키는 `.streamlit/secrets.toml`에 저장하고 `.gitignore`에 추가
- [ ] 에러 발생 시 사용자에게는 친절한 한글 메시지 (`st.error("단지를 찾을 수 없습니다. 검색어를 확인해주세요.")`)
- [ ] 모든 금액 표기는 "만원" 또는 "억" 단위로 변환 후 표시 (`498000 → 49억 8000만원`)
- [ ] 자치구 한글명은 `gu_codes_realty.gu_name`에서 가져오기 (오타·표기 통일)
- [ ] DB 연결은 `@st.cache_resource`, 데이터 조회는 `@st.cache_data(ttl=3600)` 활용
- [ ] PDF 한글 깨짐 방지 — WeasyPrint에 NotoSans KR 폰트 명시
- [ ] 1280×800 사무실 모니터에서 가로 스크롤 발생 X
- [ ] 모든 차트에 "출처: 국토교통부 실거래가 공개시스템 (2021-01 ~ 2026-05)" 워터마크

---

## 테스트 방법

```bash
# 1. 의존성 설치
cd app
pip install -r requirements.txt

# 2. 비밀번호 설정 (최초 1회)
mkdir -p .streamlit
cat > .streamlit/secrets.toml <<EOF
APP_PASSWORD = "사무실비밀번호"
EOF

# 3. 로컬 실행
streamlit run app.py

# 4. 브라우저: http://localhost:8501
```

### 수동 검증 시나리오
- [ ] "엘시티" 검색 → 브리핑 3초 내 로드
- [ ] PDF 다운로드 → A4 인쇄 시 깨지지 않음
- [ ] 존재하지 않는 단지 "asdf" → 친절한 에러 메시지
- [ ] 비밀번호 틀리면 다시 입력 화면
- [ ] 새 탭에서 열어도 비밀번호 다시 묻기

---

## 배포 방법

**원칙: 배포하지 않는다.** 사무실 PC에서만 로컬 실행.

### 사무실 PC 자동 시작 (선택)
- Windows: `streamlit run app.py` 바로가기를 시작프로그램에 등록
- 브라우저 즐겨찾기: `http://localhost:8501`

### Phase 3 공유 URL (선택)
- 공유 URL이 필요해지면 `localtunnel` / `cloudflared` 임시 터널로 외부 노출
- 정식 호스팅 필요 시 → 별도 PRD 분리

---

## 의존성 (requirements.txt)

```
streamlit>=1.40
pandas>=2.0
plotly>=5.20
weasyprint>=62
folium>=0.16
streamlit-folium>=0.20
jinja2>=3.1
```

---

## 환경변수

| 변수명 | 설명 | 어디서 발급 |
|--------|------|------------|
| APP_PASSWORD | 공용 로그인 비밀번호 | 본인이 정함 |
| DB_PATH | bptc_realestate.db 경로 | 기본값: `../02_데이터베이스/bptc_realestate.db` |
| USER_DB_PATH | briefing_app.db 경로 (Phase 2부터) | 기본값: `./briefing_app.db` |

> `.streamlit/secrets.toml`에 저장. 절대 GitHub에 올리지 마세요.

---

## [NEEDS CLARIFICATION]

- [ ] WeasyPrint Windows 설치 — GTK 의존성 문제 시 대안 (Playwright 헤드리스 Chrome) 검토
- [ ] 단지 좌표 부재 — 도로명을 카카오/네이버 지오코딩으로 변환할지, 자치구 중심점만 사용할지
- [ ] 매칭 점수 가중치 초기값 (예산 30 / 평형 20 / 학군 20 / 거래 15 / 신축 15) — 실사용 후 튜닝
- [ ] PDF 보관 기간 — 30일 자동 삭제 vs 영구 보관
- [ ] 공공데이터 월별 갱신 자동화 — 국토부 API 직접 호출 vs CSV 수동 교체
