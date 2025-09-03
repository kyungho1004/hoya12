# -*- coding: utf-8 -*-
# 항암제/항생제 데이터 (일부 발췌·요약: 보호자 친화적 표기)
ANTICANCER = {
    # Hematologic
    "ARA-C": {"alias": "시타라빈", "aes": ["골수억제", "구역", "발열"]},
    "Daunorubicin": {"alias": "다우노루비신", "aes": ["심독성", "탈모", "골수억제"]},
    "Idarubicin": {"alias": "이다루비신", "aes": ["심독성", "골수억제"]},
    "Cyclophosphamide": {"alias": "사이클로포스파마이드", "aes": ["출혈성 방광염", "골수억제"]},
    "Etoposide": {"alias": "에토포사이드", "aes": ["저혈압", "골수억제"]},
    "Fludarabine": {"alias": "플루다라빈", "aes": ["면역저하", "감염 위험 ↑"]},
    "Hydroxyurea": {"alias": "하이드록시우레아", "aes": ["골수억제", "피부 변화"]},
    "MTX": {"alias": "메토트렉세이트", "aes": ["간독성", "구내염", "신독성", "광과민"]},
    "ATRA": {"alias": "베사노이드(트레티노인)", "aes": ["분화증후군", "피부증상", "두통", "설사"]},
    "G-CSF": {"alias": "그라신", "aes": ["뼈통증", "발열 반응"]},

    # CML/CLL
    "Imatinib": {"alias": "이미티닙", "aes": ["부종", "근육통"]},
    "Dasatinib": {"alias": "다사티닙", "aes": ["흉막삼출", "혈소판 감소"]},
    "Nilotinib": {"alias": "닐로티닙", "aes": ["QT 연장", "고혈당"]},

    # Solid tumors (subset)
    "Cisplatin": {"alias": "시스플라틴", "aes": ["신독성", "귀독성", "구토"]},
    "Carboplatin": {"alias": "카보플라틴", "aes": ["골수억제"]},
    "Oxaliplatin": {"alias": "옥살리플라틴", "aes": ["말초신경병증", "한랭 과민"]},
    "Paclitaxel": {"alias": "파클리탁셀", "aes": ["말초신경병증", "과민반응"]},
    "Docetaxel": {"alias": "도세탁셀", "aes": ["부종", "점막염"]},
    "Gemcitabine": {"alias": "젬시타빈", "aes": ["골수억제", "발열"]},
    "Pemetrexed": {"alias": "페메트렉시드", "aes": ["골수억제", "피부발진"]},
    "5-FU": {"alias": "5-FU(플루오로우라실)", "aes": ["구내염", "설사", "수족증후군"]},
    "Capecitabine": {"alias": "카페시타빈", "aes": ["수족증후군", "설사"]},
    "Irinotecan": {"alias": "이리노테칸", "aes": ["설사(조기/지연)", "골수억제"]},
    "Trastuzumab": {"alias": "트라스투주맙", "aes": ["심기능 저하"]},
    "Bevacizumab": {"alias": "베바시주맙", "aes": ["상처치유지연", "고혈압"]},
    "Sorafenib": {"alias": "소라페닙", "aes": ["수족증후군", "고혈압"]},
    "Lenvatinib": {"alias": "렌바티닙", "aes": ["고혈압", "단백뇨"]},
    "Sunitinib": {"alias": "수니티닙", "aes": ["고혈압", "피로"]},
    "Pazopanib": {"alias": "파조파닙", "aes": ["간독성", "고혈압"]},
    "Regorafenib": {"alias": "레고라페닙", "aes": ["수족증후군", "고혈압"]},
    "Pembrolizumab": {"alias": "펨브롤리주맙", "aes": ["면역관련 부작용(간염/폐렴 등)"]},
    "Nivolumab": {"alias": "니볼루맙", "aes": ["면역관련 부작용"]},
    "Temozolomide": {"alias": "테모졸로마이드", "aes": ["골수억제"]},
    "Ifosfamide": {"alias": "이포스파마이드", "aes": ["신경독성", "출혈성 방광염"]},
    "Doxorubicin": {"alias": "독소루비신", "aes": ["심독성", "탈모"]},
    "Cabazitaxel": {"alias": "카바지탁셀", "aes": ["골수억제"]},
    # Pediatric/others used in sarcomas
    "Vincristine": {"alias": "빈크리스틴", "aes": ["말초신경병증", "변비"]},
    "Asparaginase": {"alias": "아스파라기나제", "aes": ["췌장염", "혈전"]},
}

# 항생제(계열/요약 주의) — 세대 대신 보호자 친화적 요약
ABX_GUIDE = {
    "페니실린/아목시/암피": ["발진", "설사", "드물게 아나필락시스"],
    "세팔로스포린": ["교차 과민(페니실린과)", "설사"],
    "퀴놀론": ["힘줄염/파열", "QT 연장", "광과민"],
    "마크롤라이드(아지스로마이신 등)": ["QT 연장", "와파린 상호작용"],
    "아미노글리코사이드": ["신독성", "귀독성"],
    "카바페넴": ["경련 위험(고용량)", "광범위 내성에 주의"],
    "테트라사이클린": ["치아 변색(소아)", "광과민"],
    "설폰아마이드": ["피부 발진", "광과민"],
}
