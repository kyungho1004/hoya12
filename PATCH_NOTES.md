# BloodMap v3.16.0 패치 노트

## 핵심
- ✅ PDF 한글 폰트 **자동 등록 유지** (폰트 파일 넣으면 즉시 적용) — `/fonts` 폴더 사용
- ✅ **중복 저장 방지 강화**: 동일 `user_key + timestamp` 발생 시 timestamp에 suffix 부여
- ✅ **page_config 단일화**: 엔트리포인트에서 제거 → `app.py`에서만 설정
- ✅ **소아 해석 문구 진단별 보강**: ALL, AML/APL, 유잉, 골육종 특화 문구 추가
- ✅ **특수검사 확장**: Ferritin, LDH, Uric acid, ESR, Retic(%), β2-microglobulin, Coombs 입력 + 간단 해석
- ✅ **그래프 확장**: 위 특수검사 수치도 기록 시 추이 그래프 자동 렌더

## 사용 팁
- PDF 한글 폰트: `/fonts` 폴더에 `NotoSansKR-Regular.ttf` 또는 `NanumGothic.ttf` 넣으면 자동 적용됩니다.
- 그래프: 동일 **별명#PIN**으로 저장한 기록이 쌓이면 결과 탭에서 자동 표시됩니다.

## 파일 구조 변경
- `bloodmap_app/utils.py`: pediatric_guides(진단 반영), 해석 함수 추가, PDF 폰트 함수 개선
- `bloodmap_app/graphs.py`: DEFAULT_Y_LIST 확장, 동적 플로팅
- `bloodmap_app/app.py`: 특수검사 UI 추가, 저장 중복 방지, 진단 반영 소아 가이드, page_config 단일화
- `streamlit_app.py`: 임포트 래퍼 + page_config 제거


# BloodMap v3.17.0 패치 노트 (소아/진단별 + 특수검사 대폭 확장)

## 소아/진단별 가이드 보강
- ALL: 유지요법(6-MP/MTX) 복용 누락 주의, 발열 시 즉시 보고
- AML/APL: 점막출혈·멍 증가 시 임의 중단 금지, 의료진 상의
- 유잉육종: VAC/IE 주기 중 FN 교육 + 신장기능 모니터
- 골육종: 고용량 MTX 수분/알칼리뇨/르코보린 구조요법, 시스플라틴 이독성 관찰
- 횡문근육종: 빈크리스틴 말초신경증상·변비 예방 교육
- HLH: 발열 지속/의식저하 시 즉시 내원, ferritin/TG/피브리노겐 추적

## 특수검사(+)
- 새 입력: **AST, ALT, ALP, GGT, Total bilirubin, Na, K, Ca, Mg, Phos, INR, aPTT, Fibrinogen, D-dimer, Triglycerides, Lactate**
- 간단 해석 배너 자동 표시(비특이/경고 기준): 전해질·간수치·응고·대사

## 그래프
- 위 특수검사들도 저장 시 **추이 그래프 자동 표시**(별명#PIN 기준)

## 기타
- 버전: v3.17.0


# v3.17.1 핫픽스
- 일부 환경에서 `bloodmap_app.utils`가 **디렉토리(패키지)** 로 인식되어 `ImportError`가 발생하던 문제 수정.
- 헬퍼 모듈명을 `helpers.py`로 변경하고, 앱은 `from .helpers import ...`를 사용하도록 수정.


# v3.17.2 핫픽스
- `ModuleNotFoundError: matplotlib` 해결: `requirements.txt`에 `matplotlib>=3.8` 추가.
- 그래프 모듈이 matplotlib 미설치 환경에서도 **Streamlit line_chart**로 자동 폴백하도록 수정.


# v3.17.3 핫픽스
- 일부 환경에서 `drug_data.REGIMENS`가 누락되어 `AttributeError`가 발생하던 문제 수정.
- 앱이 `REGIMENS`/`ANTIBIOTICS_BY_CLASS`/`ABX_CLASS_TIPS` 부재 시 **안전한 기본값**으로 자동 폴백.
