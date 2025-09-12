# -*- coding: utf-8 -*-
from typing import Dict, List

def lab_diet_guides(labs: Dict, heme_flag: bool = False) -> List[str]:
    """
    피수치 기반 식이가이드(예시)
    labs: {'Alb':3.1, 'K':3.2, ...}
    heme_flag: 혈액암 카테고리 여부(철분+비타민C 경고)
    """
    L: List[str] = []

    def add(title, foods, caution=None):
        if foods:
            L.append(f"{title} → 권장 예시: {', '.join(foods)}")
        if caution:
            L.append(f"주의: {caution}")

    Alb = labs.get("Alb"); K = labs.get("K"); Hb = labs.get("Hb"); Na = labs.get("Na"); Ca = labs.get("Ca")
    Glu = labs.get("Glu"); AST=labs.get("AST"); ALT=labs.get("ALT"); Cr=labs.get("Cr"); BUN=labs.get("BUN")
    UA=labs.get("UA"); CRP=labs.get("CRP"); ANC=labs.get("ANC"); PLT=labs.get("PLT")

    if Alb is not None and Alb < 3.5:
        add("알부민 낮음", ["달걀","연두부","흰살 생선","닭가슴살","귀리죽"])
    if K is not None and K < 3.5:
        add("칼륨 낮음", ["바나나","감자","호박죽","고구마","오렌지"])
    if Hb is not None and Hb < 10:
        add("Hb 낮음(빈혈)", ["소고기","시금치","두부","달걀 노른자","렌틸콩"],
            caution="보충제는 식품이 아닙니다. (혈액암인 경우 철분제+비타민C 복용은 반드시 주치의와 상의)")
        if heme_flag:
            L.append("⚠️ 혈액암 환자: 철분제 + 비타민C 병용은 흡수 촉진 → 반드시 주치의와 상의 후 결정")
    if Na is not None and Na < 135:
        add("나트륨 낮음", ["전해질 음료","미역국","바나나","오트밀죽","삶은 감자"])
    if Ca is not None and Ca < 8.5:
        add("칼슘 낮음", ["연어통조림","두부","케일","브로콜리"], caution="참깨는 제외")
    if Glu is not None and Glu >= 140:
        add("혈당 높음", ["현미/귀리","두부 샐러드","채소 수프","닭가슴살","사과(소과)"],
            caution="당분 많은 간식/음료 피하기")
    if (Cr is not None and Cr > 1.2) or (BUN is not None and BUN > 20):
        add("신장 수치 상승", ["물/보리차 자주 조금씩","애호박/오이 수프","양배추찜","흰쌀죽","배/사과(소량)"],
            caution="단백질 과다 섭취·짠 음식 피하고, 탈수 주의")
    if (AST is not None and AST >= 50) or (ALT is not None and ALT >= 55):
        add("간수치 상승(AST/ALT)", ["구운 흰살생선","두부","삶은 야채","현미죽(소량)","올리브오일 드레싱 샐러드"],
            caution="기름진/튀김/술 피하기")
    if UA is not None and UA > 7:
        add("요산 높음", ["우유/요거트","달걀","감자","채소류","과일(체리 등)"],
            caution="내장·멸치·맥주 등 퓨린 높은 음식 제한")
    if CRP is not None and CRP >= 3:
        add("CRP 상승(염증)", ["토마토","브로콜리","블루베리","연어(완전 익히기)","올리브오일"],
            caution="생식 금지, 충분한 수분")
    if ANC is not None and ANC < 500:
        add("ANC<500 (호중구감소)", ["흰죽","계란찜(완숙)","연두부","잘 익힌 고기/생선","통조림 과일(시럽 제거)"],
            caution="생채소 금지 · 모든 음식은 완전히 익히기 또는 전자레인지 30초↑ · 멸균/살균 식품 권장 · 남은 음식은 2시간 지나면 폐기 · 껍질 있는 과일은 주치의와 상의")
    if PLT is not None and PLT < 20000:
        add("혈소판 낮음(PLT<20k)", ["계란찜","두부","바나나","오트밀죽","미역국"],
            caution="딱딱/자극 음식·술 피하고, 양치 시 부드러운 칫솔 사용")

    return L


def peds_diet_guides(symptoms: dict, temp_c: float | None, age_months: int | None) -> list[str]:
    """
    소아 증상 기반 간단 식이가이드(일상/질환 모드 공용)
    - 증상 키 예시: {"콧물": "...", "기침": "...", "설사": "...", "발열": "...", "구토": "있음/없음"}
    - temp_c는 선택값(없으면 규칙 중 발열 항목만 증상 텍스트로 판단)
    반환: 권장/주의 문구 리스트
    """
    s = symptoms or {}
    out: list[str] = []

    def add(line: str): 
        if line and line not in out:
            out.append(line)

    fever_txt = (s.get("발열") or "").strip()
    cough_txt = (s.get("기침") or "").strip()
    rhin_txt  = (s.get("콧물") or "").strip()
    diarr_txt = (s.get("설사") or "").strip()
    vomi_txt  = (s.get("구토") or "없음").strip()

    # 공통 수분 보충
    if temp_c and temp_c >= 38.5 or (fever_txt.startswith("38.5") or fever_txt.startswith("39")):
        add("고열 시 수분보충: 미지근한 물/전해질 음료를 소량씩 자주")
        add("속이 불편하면 자극적/기름진 음식 피하고, 흰죽·국수·바나나 등 담백한 식단 권장")

    # 기침/콧물
    if cough_txt != "없음" or rhin_txt != "없음":
        add("따뜻한 국물(미역국/닭곰탕/맑은 된장국)과 충분한 수분 섭취")
        if age_months is not None and age_months < 12:
            add("생꿀 금지(만 1세 미만 보툴리눔 위험) — 배숙 등은 설탕/배만 사용")
        else:
            add("꿀차/배숙 등 따뜻한 음료 가능(과다 당분은 피하기)")

    # 구토/설사
    if vomi_txt == "있음" or "설사" in diarr_txt or diarr_txt in ["물설사","피 섞임"]:
        add("구토·설사 시: 수분·전해질 보충(ORS), 소량씩 자주")
        add("BRAT 식단 응용: 흰죽/바나나/사과퓨레/식빵/감자·고구마 삶은 것")
        add("우유·튀김·매운 음식은 증상 호전될 때까지 일시 제한")
        if diarr_txt == "피 섞임":
            add("혈변 동반 시 병원 상담 권장")

    # 일상 위생/안전 (보호자 공통 가이드)
    add("모든 음식은 충분히 익혀 제공하고, 조리 후 2시간이 지나면 폐기")
    add("과일·채소는 흐르는 물에 깨끗이 세척해 껍질째 제공 시 잘 씻기")

    return out
