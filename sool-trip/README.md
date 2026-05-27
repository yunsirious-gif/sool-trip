# 술여행 (Sool Trip) — 지역 기반 전통주 여행지 추천

전국 시/도·시/군/구를 선택하면 그 지역의 **양조장 · 관광지 · 맛집 · 축제**를 모아 보여주고,
Gemini AI가 취향에 맞춰 **하루 코스**를 짜주는 Streamlit 앱.

## 데이터 소스
- 양조장 / 전통주: [공공데이터포털 — 한국농수산식품유통공사 데이터셋 2종](https://www.data.go.kr/)
- 관광지 / 맛집 / 축제: 한국관광공사 TourAPI 4.0
- 코스 추천: Google Gemini 2.0 Flash

## 설치
```bash
cd sool-trip
pip install -r requirements.txt
```

## 최초 1회 — 데이터 적재
```bash
python scripts/load_data.py
```
→ `data/breweries.db` 생성 (양조장 462곳, 술 1,188종)

## 실행
```bash
streamlit run app.py
```

## 폴더 구조
```
sool-trip/
├── app.py                # 홈 (지역 선택)
├── pages/
│   ├── 1_지역_탐색.py    # 양조장·관광지·맛집·축제 4탭
│   └── 2_AI_코스_추천.py # Gemini 코스 생성
├── lib/                  # 도메인 로직
├── scripts/load_data.py  # CSV → SQLite 적재
├── data/                 # SQLite + 원본 CSV
└── .env                  # API 키 (gitignore)
```

## API 키
`.env`에 두 키가 등록되어 있어야 합니다.
- `PUBLIC_DATA_API_KEY` — 공공데이터포털 일반 인증키 (TourAPI 활용신청 필요)
- `GEMINI_API_KEY` — https://aistudio.google.com/apikey

## Streamlit Community Cloud 배포

1. **GitHub 레포 만들기** — 이 폴더(또는 상위 폴더)를 push.
   `.env` / `data/breweries.db`는 `.gitignore`로 제외됨 (DB는 첫 실행 시 자동 빌드).
2. **https://share.streamlit.io** 접속 → **New app**.
3. 레포 / 브랜치 선택, **Main file path**: `sool-trip/app.py` (저장소 루트가 `bptc-data-pack-main`인 경우).
4. **Advanced settings → Secrets** 에 아래 두 줄 붙여넣기:
   ```toml
   GEMINI_API_KEY = "발급받은_키"
   PUBLIC_DATA_API_KEY = "발급받은_키"
   ```
5. **Deploy** 클릭 — 1~2분 후 `https://<your-app>.streamlit.app` 으로 접속 가능.

> 첫 실행 시 CSV → SQLite 빌드가 자동 실행됩니다 (`lib/db.py::_ensure_db`).
