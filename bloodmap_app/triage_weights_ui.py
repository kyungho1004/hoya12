# --- 간단 모드 (일반 보호자용) ---
if mode == "간단":
    groups = {
        "감염/발열": ["발열 38.0–38.4","고열 ≥38.5","CRP ≥10","ANC<500","ANC 500–999"],
        "피·출혈": ["혈소판 <20k","점상출혈","혈변","흑색변","혈뇨"],
        "호흡·심장": ["호흡곤란","흉통","HR>130"],
        "신경": ["의식저하","번개두통","시야 이상"],
        "소변·탈수": ["소변량 급감","지속 구토"],
        "기타": []
    }

    # 라벨 치환(쉬운 질문형)
    label_map = {
        "ANC<500":"🩸 호중구가 매우 낮다고 들었나요?",
        "ANC 500–999":"🩸 호중구가 조금 낮다고 들었나요?",
        "발열 38.0–38.4":"🌡️ 미열(38.0~38.4)인가요?",
        "고열 ≥38.5":"🌡️ 38.5℃ 이상 고열인가요?",
        "혈소판 <20k":"🧪 멍/코피/코딱지 피가 잦나요?",
        "중증빈혈 Hb<7":"❤️ 창백·어지럼이 두드러지나요?",
        "CRP ≥10":"🧪 염증수치(CRP)가 높다고 했나요?",
        "HR>130":"💓 가만히 있어도 맥박이 >130인가요?",
        "혈뇨":"🚽 소변에 피가 보이나요?",
        "흑색변":"🚽 변이 까맣게 변했나요?",
        "혈변":"🚽 변에 선홍빛 피가 섞이나요?",
        "흉통":"🫁 가슴이 아픈가요?",
        "호흡곤란":"🫁 숨이 차거나 힘든가요?",
        "의식저하":"🧠 깨우기 어렵거나 처지나요?",
        "소변량 급감":"🥤 소변이 확 줄었나요?",
        "지속 구토":"🥤 마신 걸 계속 토하나요?",
        "점상출혈":"🔴 바늘끝같은 붉은 점이 퍼져 있나요?",
        "번개두통":"🧠 ‘벼락처럼’ 심한 두통이 갑자기?",
        "시야 이상":"🧠 시야가 흐리거나 겹쳐 보이나요?"
    }

    with st.container(border=True):
        for grp, items in groups.items():
            if not items: 
                continue
            with st.expander(grp, expanded=True if grp in ["감염/발열","호흡·심장"] else False):
                cols = st.columns(3)
                for i, name in enumerate(items):
                    with cols[i % 3]:
                        q = label_map.get(name, name)
                        sel = st.radio(q, ["없음","약간","뚜렷"],
                            index=0 if cfg.signals[name]<=0.1 else (1 if cfg.signals[name] < 4 else 2),
                            key=f"{state_key_prefix}_simple_{name}")
                        cfg.signals[name] = 0.0 if sel=="없음" else (2.5 if sel=="약간" else 5.0)

                        # 툴팁(전문가 설명)
                        if st.checkbox("ℹ️ 자세히", key=f"{state_key_prefix}_tip_{name}", value=False):
                            st.caption(f"전문가용: '{name}' 신호 강도는 프리셋 가중치와 곱해져 계산됩니다.")

    # 점수/권고: 좌·우 분리
    score, contrib, _ = compute_score(cfg)
    cL, cR = st.columns([2,1])
    with cL:
        _render_header(score, contrib)
    with cR:
        st.markdown("#### 권고")
        if score >= 80:
            st.error("지금 응급실 권고\n- 마스크 착용, 최근 복용약 메모 지참")
        elif score >= 60:
            st.warning("오늘 빠른 외래 + 집에서 수분·증상 관찰")
        elif score >= 40:
            st.info("1–2일 내 재평가 예약 + 안내문 제공")
        else:
            st.success("가정 관리 + 악화 시 바로 연락")
