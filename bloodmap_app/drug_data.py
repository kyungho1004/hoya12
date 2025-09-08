# -*- coding: utf-8 -*-
# 표적치료제/면역항암제 우선 병기
def ko(name: str) -> str:
    m = {
        "Osimertinib":"오시머티닙(Osimertinib)","Gefitinib":"게피티닙(Gefitinib)","Erlotinib":"얼로티닙(Erlotinib)","Afatinib":"아파티닙(Afatinib)",
        "Alectinib":"알렉티닙(Alectinib)","Crizotinib":"크리조티닙(Crizotinib)","Brigatinib":"브리가티닙(Brigatinib)","Lorlatinib":"롤라티닙(Lorlatinib)",
        "Capmatinib":"캡마티닙(Capmatinib)","Tepotinib":"테포티닙(Tepotinib)","Selpercatinib":"셀퍼카티닙(Selpercatinib)","Pralsetinib":"프랄세티닙(Pralsetinib)",
        "Entrectinib":"엔트렉티닙(Entrectinib)","Larotrectinib":"라로트렉티닙(Larotrectinib)","Sotorasib":"소토라십(Sotorasib)","Adagrasib":"아다가라십(Adagrasib)",
        "Bevacizumab":"베바시주맙(Bevacizumab)","Ramucirumab":"라무시루맙(Ramucirumab)","Pembrolizumab":"펨브롤리주맙(Pembrolizumab)",
        "Nivolumab":"니볼루맙(Nivolumab)","Atezolizumab":"아테졸리주맙(Atezolizumab)","Durvalumab":"더발루맙(Durvalumab)","Ipilimumab":"이필리무맙(Ipilimumab)",
        "Trastuzumab":"트라스투주맙(Trastuzumab)","Pertuzumab":"퍼투주맙(Pertuzumab)","Ado-trastuzumab emtansine":"T-DM1(Ado-trastuzumab emtansine)",
        "Trastuzumab deruxtecan":"T-DXd(Trastuzumab deruxtecan)","Tucatinib":"투카티닙(Tucatinib)","Neratinib":"네라티닙(Neratinib)",
        "Sacituzumab govitecan":"사시투주맙 고비테칸(Sacituzumab govitecan)","Alpelisib":"알펠리십(Alpelisib)",
        "Dabrafenib":"다브라페닙(Dabrafenib)","Trametinib":"트라메티닙(Trametinib)","Vemurafenib":"베무라페닙(Vemurafenib)","Encorafenib":"엔코라페닙(Encorafenib)","Binimetinib":"비니메티닙(Binimetinib)",
        "Belzutifan":"벨주티판(Belzutifan)","Cabozantinib":"카보잔티닙(Cabozantinib)","Lenvatinib":"렌바티닙(Lenvatinib)","Sunitinib":"수니티닙(Sunitinib)","Pazopanib":"파조파닙(Pazopanib)",
        "Axitinib":"악시티닙(Axitinib)","Tivozanib":"티보자닙(Tivozanib)","Everolimus":"에베로리무스(Everolimus)",
        "Olaparib":"올라파립(Olaparib)","Niraparib":"니라파립(Niraparib)","Rucaparib":"루카파립(Rucaparib)","Mirvetuximab soravtansine":"미르베툭시맙 소라브탄신(Mirvetuximab soravtansine)",
        "Zolbetuximab":"졸베투시맙(Zolbetuximab)","Dostarlimab":"도스타릴맙(Dostarlimab)",
        "Enfortumab vedotin":"엔포투맙 베도틴(Enfortumab vedotin)","Erdafitinib":"에르다피티닙(Erdafitinib)",
        "Pemigatinib":"페미가티닙(Pemigatinib)","Futibatinib":"푸티바티닙(Futibatinib)","Ivosidenib":"이보시데닙(Ivosidenib)","Zanidatamab":"자니다타맙(Zanidatamab)",
        "Selumetinib":"셀루메티닙(Selumetinib)","Ripretinib":"리프레티닙(Ripretinib)","Regorafenib":"레고라페닙(Regorafenib)",
        "Cetuximab":"세툭시맙(Cetuximab)","Panitumumab":"파니투무맙(Panitumumab)","Tisotumab vedotin":"티소투맙 베도틴(Tisotumab vedotin)",
        "Alectinib":"알렉티닙(Alectinib)","Amivantamab":"아미반타맙(Amivantamab)","Mobocertinib":"모보서티닙(Mobocertinib)",
        "Larotrectinib":"라로트렉티닙(Larotrectinib)","Entrectinib":"엔트렉티닙(Entrectinib)","Fruquintinib":"프루퀸티닙(Fruquintinib)"
    }
    return m.get(name, name)

# 고형암: 표적약물 중심으로 확장 (세포독성 약물은 목록 최소화)
solid_targeted = {
    "폐암(Lung cancer)": [
        # EGFR
        "Osimertinib","Gefitinib","Erlotinib","Afatinib",
        # ALK/ROS1
        "Alectinib","Crizotinib","Brigatinib","Lorlatinib","Entrectinib",
        # METex14
        "Capmatinib","Tepotinib",
        # RET
        "Selpercatinib","Pralsetinib",
        # NTRK
        "Larotrectinib","Entrectinib",
        # KRAS G12C
        "Sotorasib","Adagrasib",
        # EGFR Ex20ins/HER3
        "Amivantamab","Mobocertinib",
        # BRAF
        "Dabrafenib","Trametinib",
        # ICI
        "Pembrolizumab","Nivolumab","Atezolizumab","Durvalumab"
    ],
    "유방암(Breast cancer)": [
        "Trastuzumab","Pertuzumab","Ado-trastuzumab emtansine","Trastuzumab deruxtecan","Tucatinib","Neratinib",
        "Palbociclib","Ribociclib","Abemaciclib",
        "Alpelisib",
        "Sacituzumab govitecan"
    ],
    "대장암(Colorectal cancer)": [
        "Cetuximab","Panitumumab","Bevacizumab","Ramucirumab","Regorafenib","Fruquintinib",
        "Pembrolizumab","Nivolumab","Encorafenib"
    ],
    "위암(Gastric cancer)": [
        "Trastuzumab","Trastuzumab deruxtecan","Ramucirumab","Pembrolizumab","Nivolumab","Zolbetuximab"
    ],
    "간암(HCC)": [
        "Lenvatinib","Sorafenib","Regorafenib","Cabozantinib","Atezolizumab","Bevacizumab","Durvalumab"
    ],
    "담도암(Cholangiocarcinoma)": [
        "Pemigatinib","Futibatinib","Ivosidenib","Zanidatamab","Pembrolizumab","Durvalumab"
    ],
    "췌장암(Pancreatic cancer)": [
        "Olaparib"
    ],
    "자궁내막암(Endometrial cancer)": [
        "Dostarlimab","Pembrolizumab","Lenvatinib"
    ],
    "난소암": [
        "Olaparib","Niraparib","Rucaparib","Mirvetuximab soravtansine","Bevacizumab"
    ],
    "자궁경부암": [
        "Pembrolizumab","Tisotumab vedotin","Bevacizumab"
    ],
    "신장암(RCC)": [
        "Cabozantinib","Lenvatinib","Axitinib","Sunitinib","Pazopanib","Tivozanib","Belzutifan",
        "Nivolumab","Pembrolizumab","Ipilimumab"
    ],
    "피부암(흑색종)": [
        "Pembrolizumab","Nivolumab","Ipilimumab","Dabrafenib","Trametinib","Vemurafenib","Encorafenib","Binimetinib"
    ],
    "갑상선암": [
        "Lenvatinib","Sorafenib","Selpercatinib","Pralsetinib","Dabrafenib","Trametinib"
    ],
    "뇌종양(Glioma)": [
        "Bevacizumab"
    ],
    "식도암": [
        "Pembrolizumab","Nivolumab","Trastuzumab","Ramucirumab"
    ],
    "방광암": [
        "Pembrolizumab","Nivolumab","Avelumab","Enfortumab vedotin","Erdafitinib"
    ],
    "전립선암": [
        # 표적/신호전달제 우선
        "Abiraterone","Enzalutamide","Apalutamide","Olaparib"
    ]
}
