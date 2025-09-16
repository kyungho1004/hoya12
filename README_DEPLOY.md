# 설치/실행
1) 압축 풀기
2) 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
3) 실행
   ```bash
   streamlit run app/app.py
   ```

## 모드 전환
- 사이드바에서 값 입력.
- `st.session_state['mode'] = '암'`(또는 'cancer','onco')가 들어오면 암 화면(그래프)로 전환되어 번들 섹션이 숨겨집니다.