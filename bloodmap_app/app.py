
import streamlit as st

GOOD = "🟢"
WARN = "🟡"
DANGER = "🚨"

def _b(txt: str) -> str:
    return txt.replace("{GOOD}", GOOD).replace("{WARN}", WARN).replace("{DANGER}", DANGER)

# === Comprehensive (curated) chemo AE database for pediatric/hem-onc contexts ===
# Scope: core leukemia/lymphoma/solid regimen agents + APL(ATRA/ATO) + platinums + vincas + anthracyclines + alkylators + topoisomerase inhibitors + TKI
CHEMO_DB = {
    # Already provided earlier
    "6-MP (Mercaptopurine) / 6-머캅토퓨린": {
        "aka": ["6-MP", "Mercaptopurine", "메르캅토퓨린"],
        "effects": {
            "common": ["{WARN} 피로, 오심·구토, 식욕저하", "{WARN} 구내염/입안 통증", "{WARN} 발진/가려움"],
            "blood": ["{DANGER} 골수억제(호중구↓·혈소판↓·빈혈) — FN 위험"],
            "hepatic": ["{WARN} AST/ALT·빌리루빈 상승", "{DANGER} 약물성 간손상/담즙울체 드묾"],
            "metabolic": ["{WARN} 고요산혈증 드묾 — 관절통 주의"],
            "rare": ["{WARN} 췌장염 드묾(상복부 통증/구토)"],
        },
        "monitor": ["CBC 주기적(초기 주 1회→안정 시 연장)", "AST/ALT/T.bil, ALP"],
        "risk": ["{DANGER} TPMT/NUDT15 결핍: 중증 골수억제 — 용량 대폭 감량 필요(의료진)"],
        "when_to_call": ["🌡️ 38.5℃ 이상 발열(≥39.0℃ 즉시 병원)", "🤒 ANC<500 + 발열", "🩸 멍/코피 지속, 혈변·혈뇨", "💛 심한 황달/소변 진해짐"],
        "care": ["감염예방·손 위생", "알로퓨리놀/살라질라진 등 상호작용 보고"],
    },

    "MTX (Methotrexate) / 메토트렉세이트": {
        "aka": ["MTX", "Methotrexate", "메토트렉세이트"],
        "effects": {
            "common": ["{WARN} 구내염, 오심/구토, 식욕저하, 피로", "{WARN} 피부 건조/발진, 광과민"],
            "blood": ["{DANGER} 골수억제 — 감염·출혈 위험"],
            "hepatic": ["{WARN} AST/ALT 상승(장기 사용시 섬유화 드묾)"],
            "renal": ["{DANGER} HD-MTX: 결정뇨/신독성 — Cr↑, 소변 감소"],
            "pulmonary": ["{WARN} MTX 폐렴(비감염성) 드묾 — 마른기침·호흡곤란"],
            "neuro": ["{WARN} 고용량·IT: 경련/혼동/백질병증 드묾"],
        },
        "monitor": ["CBC, AST/ALT, Cr/eGFR", "HD-MTX: MTX 농도 + 요알칼리화/수액 + 류코보린 구제"],
        "risk": ["NSAIDs, TMP-SMX, PPI 병용 시 농도↑·독성↑ 가능"],
        "when_to_call": ["🌡️ 발열 기준 동일", "💧 소변 급감/부종/심한 구토", "😮‍💨 심한 기침/호흡곤란/저산소"],
        "care": ["HD-MTX 수액/알칼리화/류코보린 준수", "구내염 예방: 구강위생·자극식 피하기"],
    },

    "ATRA (Tretinoin, Vesanoid) / 베사노이드": {
        "aka": ["ATRA", "Tretinoin", "Vesanoid", "베사노이드"],
        "effects": {
            "common": ["{WARN} 두통, 피부 건조/발진, 입술 갈라짐", "{WARN} 광과민, 결막 자극", "{WARN} 지질 상승(중성지방/LDL)"],
            "rare": ["{WARN} 가성 뇌종양(두통/구토/시야흐림/유두부종) — 소아 주의"],
        },
        "ra_syndrome": {
            "name": "RA-분화증후군 (Differentiation Syndrome)",
            "window": "발현: 시작 후 2일~2주(간혹 더 늦게)",
            "symptoms": ["{DANGER} 발열", "{DANGER} 호흡곤란/저산소", "{DANGER} 저혈압", "{DANGER} 전신부종/체중 급증", "{WARN} 흉막·심막삼출, 신부전, 간수치 상승"],
            "risks": ["초기 WBC 높음, 신장·심폐 기저질환"],
            "actions": ["{DANGER} 의심 즉시 의료진 연락", "스테로이드 조기 투여 고려(의료진)", "산소/수액/이뇨제 등 지지요법(의료진)"],
            "caregiver": ["누우면 숨참·급격한 부종/체중증가 관찰 즉시 병원"],
        },
        "monitor": ["CBC(WBC 변화), SpO₂, 체중/부종, 간기능, 지질"],
        "when_to_call": ["😮‍💨 숨참/호흡곤란, 누우면 악화", "🧊 급격한 부종/체중 증가", "🌡️ 고열 지속, 소변 감소/저혈압 느낌"],
        "care": ["자외선 차단, 임신 금기, 용량·복약 준수"],
    },

    "ATO (Arsenic trioxide) / 비소 트리옥사이드": {
        "aka": ["ATO", "Arsenic trioxide", "비소 트리옥사이드"],
        "effects": {
            "common": ["{WARN} 피로, 오심·구토, 설사", "{WARN} 간수치 상승"],
            "cardiac": ["{DANGER} QT 연장/부정맥 — 실신, 심계항진"],
            "electrolyte": ["{WARN} K/Mg 저하 시 위험↑ — 보정 필요"],
        },
        "monitor": ["ECG(QTc), K/Mg, AST/ALT, CBC"],
        "when_to_call": ["💓 심계항진/어지러움/실신", "🌡️ 발열·무기력", "💧 소변 감소/부종"],
        "care": ["QT 연장 약물 병용 회피(의료진과 상의)", "전해질 보정 준수"],
    },

    "Cytarabine (Ara-C) / 시타라빈(아라씨)": {
        "aka": ["Cytarabine", "Ara-C", "아라씨", "시타라빈"],
        "routes": {
            "IV/SC(표준용량)": ["{WARN} 발열, 오심/구토, 설사, 구내염", "{DANGER} 골수억제", "{WARN} 발진/결막염"],
            "HDAC(고용량)": ["{DANGER} 소뇌독성: 보행실조/말 더듬/어지럼/혼동", "{WARN} 각결막염 — 스테로이드 점안 예방", "{WARN} 간수치상승, 드묾: 췌장염"],
        },
        "monitor": ["CBC, AST/ALT, Renal(HDAC), 신경학적 징후(보행/말/글씨체)"],
        "when_to_call": ["🚶‍♂️ 보행 흔들림·말 더듬·글씨체 급변", "👁️ 눈 화끈/심한 충혈", "🌡️ 발열 기준"],
        "care": ["HDAC 기간 보호자 관찰 강화", "의료진 지시대로 스테로이드 점안"],
    },

    "G-CSF (Filgrastim 등) / 그라신": {
        "aka": ["G-CSF", "Filgrastim", "Pegfilgrastim", "그라신"],
        "effects": {
            "good": ["{GOOD} ANC 상승 → 감염 위험 감소"],
            "common": ["{WARN} 뼈통증/근육통, 미열, 주사부위 통증"],
            "rare": ["{DANGER} 비장 비대/파열(좌상복부/어깨끝 통증)", "{DANGER} ARDS/호흡곤란", "{WARN} 혈뇨/단백뇨"],
        },
        "monitor": ["CBC(ANC 추적), 좌상복부 통증 시 진찰±영상"],
        "when_to_call": ["🫁 호흡곤란/저산소", "🫀 좌상복부 심통/어깨끝 통증", "🩸 혈뇨/거품뇨"],
        "care": ["뼈통증은 APAP 등으로 조절(지시)", "심한 통증·호흡곤란 즉시 병원"],
    },

    # === Anthracyclines ===
    "Doxorubicin / 도소루비신(아드리아마이신)": {
        "aka": ["Doxorubicin", "Adriamycin", "도소루비신"],
        "effects": {
            "common": ["{WARN} 오심/구토, 탈모, 구내염", "{WARN} 홍색 소변 일시적"],
            "cardiac": ["{DANGER} 누적용량-의존성 심근병증/심부전", "{WARN} 부정맥/심전도 변화"],
            "blood": ["{WARN} 골수억제"],
            "derm": ["{WARN} 주사 외상 시 조직괴사(혈관외유출)"],
        },
        "monitor": ["심장초음파(EF), ECG, CBC"],
        "when_to_call": ["💓 흉통/숨참/부종", "🛑 주사 부위 통증/부종(혈관외유출 의심)"],
        "care": ["누적용량 관리, 방사선 동시부위 주의(리콜)"],
    },

    "Daunorubicin / 다우노루비신": {
        "aka": ["Daunorubicin", "다우노루비신"],
        "effects": {
            "common": ["{WARN} 오심/구토, 구내염, 탈모"],
            "cardiac": ["{DANGER} 심독성(누적)"],
            "blood": ["{WARN} 골수억제"],
        },
        "monitor": ["심초음파, ECG, CBC"],
        "when_to_call": ["💓 흉통/호흡곤란/부종", "🩸 출혈 경향"],
        "care": ["누적용량 관리, 심독 위험인자 평가"],
    },

    # === Vinca alkaloids ===
    "Vincristine / 빈크리스틴": {
        "aka": ["Vincristine", "빈크리스틴", "VCR"],
        "effects": {
            "neuro": ["{DANGER} 말초신경병증(감각·운동) — 보행이상/수지운동 저하", "{WARN} 턱통증/신경통", "{WARN} 자율신경: 변비/장마비, 요정체"],
            "blood": ["{WARN} 골수억제는 상대적으로 경미"],
        },
        "monitor": ["신경학적 징후, 변비·장음, 보행/미세운동"],
        "when_to_call": ["🚶 보행 악화/넘어짐", "🚻 심한 변비/복부팽만", "✋ 손저림/근력저하 진행"],
        "care": ["변비 예방(수분/섬유·완하제 지시), 신경 증상 보고"],
    },

    "Vinblastine / 빈블라스틴": {
        "aka": ["Vinblastine", "빈블라스틴"],
        "effects": {
            "neuro": ["{WARN} 말초신경병증 가능"],
            "blood": ["{WARN} 골수억제 두드러짐 — 호중구↓"],
            "derm": ["{WARN} 혈관외유출 위험"],
        },
        "monitor": ["CBC, 말초신경 증상, 주사부위"],
        "when_to_call": ["🩸 멍·코피, 발열", "🛑 주사부위 통증/발적"],
        "care": ["혈관외유출 예방, 감염 예방"],
    },

    # === Alkylators ===
    "Cyclophosphamide / 사이클로포스파미드": {
        "aka": ["Cyclophosphamide", "사이클로포스파미드", "CTX"],
        "effects": {
            "common": ["{WARN} 오심/구토, 탈모", "{WARN} SIADH 드묾 — 저나트륨"],
            "blood": ["{WARN} 골수억제"],
            "uro": ["{DANGER} 출혈성 방광염(헤모시스틴 독성) — 혈뇨/배뇨통"],
        },
        "monitor": ["CBC, 소변검사(혈뇨), 수분섭취·배뇨량"],
        "when_to_call": ["🩸 혈뇨/배뇨통", "💧 소변 급감/부종", "🤢 구토 지속"],
        "care": ["수액·자주 배뇨, 고용량 시 메스나 병용(의료진)"],
    },

    "Ifosfamide / 이포스파미드": {
        "aka": ["Ifosfamide", "이포스파미드", "IFO"],
        "effects": {
            "neuro": ["{DANGER} 신경독성(혼동/졸림/환시/경련)"],
            "renal": ["{WARN} 신세뇨관 독성 — 포도당뇨/전해질 이상"],
            "uro": ["{DANGER} 출혈성 방광염"],
        },
        "monitor": ["신경상태, 소변검사, 전해질/Kidney", "메스나 병용 여부"],
        "when_to_call": ["🧠 혼동/이상행동/경련", "🩸 혈뇨/배뇨통", "💧 다뇨/다갈·저칼륨 증상"],
        "care": ["메스나 병용, 충분한 수액, 신경증상 즉시 보고"],
    },

    # === Topoisomerase inhibitors ===
    "Etoposide / 에토포사이드": {
        "aka": ["Etoposide", "에토포사이드", "VP-16"],
        "effects": {
            "common": ["{WARN} 오심/구토, 저혈압(주입속도 관련)", "{WARN} 탈모"],
            "blood": ["{WARN} 골수억제 — 호중구↓"],
            "rare": ["{WARN} 과민반응/기관지경련 드묾"],
        },
        "monitor": ["CBC, 주입 중 활력징후"],
        "when_to_call": ["🌡️ 발열, 🩸 출혈성 경향", "😵 어지럼/저혈압 증상"],
        "care": ["주입 속도 관리, 과민반응 모니터"],
    },

    # === Platinums ===
    "Cisplatin / 시스플라틴": {
        "aka": ["Cisplatin", "시스플라틴"],
        "effects": {
            "renal": ["{DANGER} 신독성 — Cr↑, Mg/K↓"],
            "neuro": ["{WARN} 말초신경병증/청력독성(이독성)"],
            "gi": ["{WARN} 심한 오심/구토"],
        },
        "monitor": ["Cr/eGFR, 전해질(Mg/K/Ca), 청력검사(오디오그램), CBC"],
        "when_to_call": ["👂 이명/청력저하", "💧 소변 감소/부종", "🤢 구토 지속"],
        "care": ["충분 수액/이뇨, 이독성 증상 즉시 보고"],
    },

    "Carboplatin / 카보플라틴": {
        "aka": ["Carboplatin", "카보플라틴"],
        "effects": {
            "blood": ["{WARN} 골수억제(혈소판↓ 두드러짐)"],
            "renal": ["{WARN} 신독성 위험 낮지만 주의"],
            "gi": ["{WARN} 오심/구토"],
        },
        "monitor": ["CBC, Cr/eGFR, 전해질"],
        "when_to_call": ["🩸 쉽게 멍·코피", "🤢 구토 지속"],
        "care": ["용량 Calvert 공식(의료진) 적용, 출혈징후 관찰"],
    },

    "Oxaliplatin / 옥살리플라틴": {
        "aka": ["Oxaliplatin", "옥살리플라틴"],
        "effects": {
            "neuro": ["{WARN} 급성 냉유발 말초신경병증(목저림/인후 경련 느낌)", "{WARN} 만성 감각저하"],
            "gi": ["{WARN} 오심/구토, 설사"],
        },
        "monitor": ["신경학적 증상, 추위 노출 반응"],
        "when_to_call": ["🥶 찬 공기/음료에 심한 목·손 저림", "감각저하 진행"],
        "care": ["투여 전후 찬음료/찬공기 회피"],
    },

    # === Asparaginase ===
    "Pegaspargase / 페가스파라게이스": {
        "aka": ["Pegaspargase", "페가스파라게이스", "PEG-ASP"],
        "effects": {
            "blood": ["{WARN} 혈전·출혈 위험(항트롬빈↓)", "{WARN} 골수억제는 상대적 적음"],
            "hepatic": ["{WARN} 간수치 상승, 고암모니아혈증 드묾"],
            "pancreas": ["{DANGER} 췌장염 — 상복부 통증/구토"],
            "metabolic": ["{WARN} 고혈당/당불내성"],
            "allergy": ["{WARN} 과민반응/아나필락시스 가능"],
        },
        "monitor": ["AT(항트롬빈), PT/aPTT, Fbg, AST/ALT, TG, Glucose, amylase/lipase"],
        "when_to_call": ["🩸 종아리 통증/붓기(혈전 의심), 흉통/호흡곤란", "🍽️ 상복부 심통/구토(췌장염)", "🤧 두드러기/호흡곤란"],
        "care": ["지질·혈당 관리, 췌장염 병력 시 주의"],
    },

    # === TKIs for CML/Ph+ ALL ===
    "Imatinib / 이마티닙": {
        "aka": ["Imatinib", "이마티닙", "Gleevec"],
        "effects": {
            "common": ["{WARN} 부종(눈꺼풀/다리), 근육통/경련, 설사, 발진"],
            "blood": ["{WARN} 골수억제"],
            "hepatic": ["{WARN} 간수치 상승"],
        },
        "monitor": ["CBC, 간기능, 체중/부종"],
        "when_to_call": ["🧊 급격한 부종/체중 증가", "🌡️ 발열·감염"],
        "care": ["복용 규칙 준수, 상호작용(강력 CYP 억제/유도) 확인"],
    },

    "Dasatinib / 다사티닙": {
        "aka": ["Dasatinib", "다사티닙", "Sprycel"],
        "effects": {
            "resp": ["{WARN} 흉막삼출/호흡곤란", "{WARN} 폐동맥고혈압 드묾"],
            "blood": ["{WARN} 골수억제"],
            "gi": ["{WARN} 설사/복통"],
        },
        "monitor": ["CBC, 흉부X-ray 또는 초음파(삼출 의심 시), 산소포화도"],
        "when_to_call": ["😮‍💨 숨참/계단 오르기 힘듦", "흉통/부종"],
        "care": ["삼출 증상 보고, 이뇨제/용량조절은 의료진 판단"],
    },

    "Nilotinib / 닐로티닙": {
        "aka": ["Nilotinib", "닐로티닙", "Tasigna"],
        "effects": {
            "cardiac": ["{DANGER} QT 연장", "{WARN} 부정맥"],
            "metabolic": ["{WARN} 고혈당/지질 변화"],
            "hepatic": ["{WARN} 간수치 상승"],
        },
        "monitor": ["ECG(QTc), K/Mg, 간기능, 혈당/지질"],
        "when_to_call": ["💓 심계항진/실신", "🌡️ 발열"],
        "care": ["QT 연장 약물 병용 회피, 공복 복용 지침 준수"],
    },
}

def render_chemo_adverse_effects(agents, route_map=None):
    st.markdown("## 항암제 부작용 가이드(광범위 확장판)")
    st.caption("Made with 💜 for Eunseo — KST 기준. 참고용이며 최종 판단은 의료진의 진료에 따릅니다.")

    if not agents:
        st.info("항암제를 선택하면 상세 부작용/모니터링 지침이 표시됩니다.")
        return

    for agent in agents:
        data = CHEMO_DB.get(agent)
        if not data:
            st.warning(f"미리 정의되지 않은 항목: {agent}")
            continue

        st.markdown(f"### {agent}")
        aka = ", ".join(data.get("aka", []))
        if aka:
            st.caption(f"다른 이름: {aka}")

        # Route-specific (e.g., Ara-C) vs structured effects
        if "routes" in data:
            route = (route_map or {}).get(agent) or "IV/SC(표준용량)"
            st.markdown(f"**투여 경로/용량:** {route}")
            for line in data["routes"].get(route, []):
                st.markdown(f"- {_b(line)}")
        else:
            eff = data.get("effects", {})
            def _section(title, key):
                items = eff.get(key) or []
                if items:
                    with st.expander(title):
                        for it in items:
                            st.markdown(f"- {_b(it)}")
            # Show ordered categories if present
            _section("흔한 부작용", "common")
            _section("혈액/골수", "blood")
            _section("간/담도", "hepatic")
            _section("신장", "renal")
            _section("폐/호흡", "resp")
            _section("폐/호흡", "pulmonary")
            _section("신경계", "neuro")
            _section("피부/주사부위", "derm")
            _section("위장관", "gi")
            _section("요로/방광", "uro")
            _section("대사", "metabolic")
            _section("심장", "cardiac")
            _section("기타/드묾", "rare")
            _section("장점/효과", "good")

        # Special: RA syndrome for ATRA; already detailed
        if agent.startswith("ATRA") and data.get("ra_syndrome"):
            ra = data["ra_syndrome"]
            with st.expander(f"⚠️ {ra['name']}"):
                st.markdown(f"- {ra['window']}")
                st.markdown("**증상 핵심:**")
                for s in ra["symptoms"]:
                    st.markdown(f"  - {_b(s)}")
                st.markdown("**위험인자:**")
                for r in ra["risks"]:
                    st.markdown(f"  - {r}")
                st.markdown("**의심 시 행동(의료진):**")
                for a in ra["actions"]:
                    st.markdown(f"  - {a}")
                st.markdown("**보호자 관찰 팁:**")
                for c in ra["caregiver"]:
                    st.markdown(f"  - {c}")

        # Monitoring / When to call / Care
        if data.get("monitor"):
            with st.expander("🧪 모니터링(검사/관찰)"):
                for m in data["monitor"]:
                    st.markdown(f"- {m}")

        if data.get("when_to_call"):
            with st.expander("🚩 즉시 연락/내원 기준"):
                for w in data["when_to_call"]:
                    st.markdown(f"- {w}")

        if data.get("care"):
            with st.expander("👐 생활수칙/주의"):
                for c in data["care"]:
                    st.markdown(f"- {c}")

    st.markdown("---")
    st.subheader("공통 요약")
    st.markdown("- 발열: **≥38.5℃ 연락**, **≥39.0℃ 또는 무기력/경련/호흡곤란/탈수 즉시 병원**")
    st.markdown("- 해열제 간격: 아세트아미노펜 **≥4h**, 이부프로펜 **≥6h** (24h 총량 초과 금지)")
    st.markdown("- **ANC<500/µL + 발열 = FN 의심** — 지체 없이 병원")
    st.markdown("- {DANGER} 증상(심계항진·실신·보행실조·혈뇨 등) 발생 시 약 복용/주입 기록과 함께 즉시 보고")

def _demo():
    st.title("피수치 가이드 — 항암제 부작용(광범위 확장판)")
    all_agents = list(CHEMO_DB.keys())
    sel = st.multiselect("항암제 선택", all_agents, default=["ATRA (Tretinoin, Vesanoid) / 베사노이드", "Cytarabine (Ara-C) / 시타라빈(아라씨)"])
    route_map = {}
    if "Cytarabine (Ara-C) / 시타라빈(아라씨)" in sel:
        route_map["Cytarabine (Ara-C) / 시타라빈(아라씨)"] = st.selectbox(
            "아라씨 제형/용량", ["IV/SC(표준용량)", "HDAC(고용량)"], key="ara_route"
        )
    render_chemo_adverse_effects(sel, route_map=route_map)

if __name__ == "__main__":
    _demo()
