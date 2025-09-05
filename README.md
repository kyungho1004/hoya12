# BloodMap / 피수치 가이드 (v3.15-pre)
- 한국시간 기준: 2025-09-05 06:17
- 모바일 꼬임 방지 CSS 적용
- 별명+PIN(4자리) 저장키로 중복 방지
- 육종 카테고리(진단명) 분리
- 항암제/항생제 한글 병기
- 특수검사 토글: 응고/보체/요검사(ACR/UPCR 자동)/지질(TG·TC)
- 보고서(md/txt/pdf) 다운로드 및 NanumGothic 폰트 사용(폰트 파일 직접 추가 필요)

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
PDF 한글 폰트가 깨지면 `fonts/NanumGothic.ttf`를 직접 추가하세요.
