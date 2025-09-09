# -*- coding: utf-8 -*-
"""Drug information: Korean name, mechanism, key side effects/cautions."""

INFO = {
    "Ara-C (Cytarabine, IV)": {
        "ko": "아라씨(시아라빈) 정맥",
        "moa": "피리미딘 유사체, DNA 합성 저해",
        "warn": "골수억제, 점막염, 발열 반응, 간기능 이상",
    },
    "ATRA (Vesanoid)": {
        "ko": "베사노이드(트레티노인)",
        "moa": "레티노산 수용체를 통한 분화 유도",
        "warn": "분화증후군(호흡곤란/부종/발열), 피부·점막 건조, 간수치 상승",
    },
    "Arsenic Trioxide": {
        "ko": "아산화비소",
        "moa": "분화 유도 및 아포토시스",
        "warn": "QT 연장, 전해질 이상, 분화증후군",
    },
    "MTX (메토트렉세이트)": {
        "ko": "메토트렉세이트",
        "moa": "DHFR 억제, 엽산 대사 차단",
        "warn": "골수억제, 간독성, 점막염, 신독성(고용량), 광과민. 엽산 보충은 개별 판단",
    },
    "6-MP (6-머캅토퓨린)": {
        "ko": "6-머캅토퓨린",
        "moa": "푸린 합성 저해",
        "warn": "골수억제, 간독성, 약물상호작용(알로푸리놀 등) 주의",
    },
    "G-CSF": {
        "ko": "그라신(G-CSF)",
        "moa": "호중구 증식/분화 촉진",
        "warn": "골통, 주사부위 통증, 드물게 비장비대. 투여 후 발열반응 가능",
    },
    "Osimertinib (EGFR TKI)": {
        "ko": "오시머티닙",
        "moa": "EGFR 변이 선택적 TKI",
        "warn": "피부발진, 설사, 드물게 간질성 폐질환",
    },
    "Alectinib (ALK TKI)": {
        "ko": "알렉티닙",
        "moa": "ALK 억제제",
        "warn": "피로, 변비, 간수치 상승",
    },
    "Crizotinib (ROS1 TKI)": {
        "ko": "크리조티닙",
        "moa": "ROS1/ALK TKI",
        "warn": "시야변화, 오심, 간기능 이상",
    },
    "Trastuzumab (HER2)": {
        "ko": "트라스투주맙",
        "moa": "HER2 표적 단클론항체",
        "warn": "심독성(좌심실 기능), 주입반응",
    },
    "Cetuximab (EGFR mAb)": {
        "ko": "세툭시맙",
        "moa": "EGFR 표적 단클론항체",
        "warn": "주입반응, 피부발진, 저마그네슘혈증",
    },
    "Pola-R-CHP": {
        "ko": "폴라투주맙 병용",
        "moa": "미세소관 억제 ADC + 화학요법",
        "warn": "말초신경병증, 골수억제",
    },
    "R-CHOP": {
        "ko": "리툭시맙 + CHOP",
        "moa": "CD20 항체 + 화학요법 병합",
        "warn": "주입반응, 감염위험, 골수억제",
    },
}

def get_info(drug: str):
    return INFO.get(drug, None)
