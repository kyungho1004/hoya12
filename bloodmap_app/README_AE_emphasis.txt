BloodMap — 항생제/항암제 '부작용 강조' 패치
=========================================
이 패치는 두 가지를 제공합니다.
1) ui_results.py: 부작용 텍스트를 스캔해서 '중요 경고'를 시각적으로 강조(🚨/🟧/🟡)합니다.
2) drug_db.py: 자주 쓰는 항생제/항암제의 대표 부작용을 보강했습니다.

적용 파일
--------
- ui_results.py (교체)
- drug_db.py (교체)

app.py에 권장 섹션(선택)
----------------------
결과 게이트에서 항암제/항생제 부작용 출력 전, 아래 3줄을 추가하면 'Top Alerts' 박스가 먼저 요약됩니다.

    from ui_results import collect_top_ae_alerts
    alerts = collect_top_ae_alerts((ctx.get("user_chemo") or []) + (ctx.get("user_abx") or []))
    if alerts: st.error("\n".join(alerts))

테스트 포인트
------------
- 항생제: Vancomycin(적색인자 증후군/AKI), Linezolid(골수억제/시신경염), Daptomycin(CPK 상승/폐침윤), 
          Cefepime(신부전 시 신경독성), Piperacillin/Tazobactam(저칼륨혈증/신장), 
          Levofloxacin(힘줄병증/QT), TMP-SMX(고칼륨/범혈구감소/SJS), Metronidazole(금주/이상감각), 
          Amoxicillin/Clavulanate(담즙정체성 간염)
- 항암제: ATRA/ATO(분화증후군/QT), Cytarabine(HDAC 소뇌독성), MTX(점막염/간·신장독성), 
          6-MP(골수억제/간독성), Anthracycline(심근독성), Cisplatin(신독성/이독성), 
          Oxaliplatin(한랭유발 말초신경병증), Paclitaxel(말초신경병증), Cyclophosphamide(출혈성 방광염),
          Ifosfamide(뇌병증), Irinotecan(설사-조기/지연), Bleomycin(폐섬유화), Rituximab(HBV 재활성화)
