# -*- coding: utf-8 -*-
from typing import Dict, List, Optional

def _foods(items: List[str]) -> str:
    return ", ".join(items)

def lab_diet_guides(labs: Dict, heme_flag: bool = False) -> List[str]:
    """
    피수치 기반 식이가이드
    - 각 수치 별 5개 음식 권장
    - ANC 단계별 가이드 포함
    - 항암(혈액암) 플래그 시 철분제 경고(음식 위주, 보충제 제외)
    """
    L: List[str] = []
    Alb = _num(labs.get("Alb")); K = _num(labs.get("K")); Hb = _num(labs.get("Hb"))
    Na  = _num(labs.get("Na"));  Ca = _num(labs.get("Ca")); Glu = _num(labs.get("Glu"))
    AST = _num(labs.get("AST")); ALT = _num(labs.get("ALT")); Cr  = _num(labs.get("Cr"))
    BUN = _num(labs.get("BUN")); CRP = _num(labs.get("CRP")); ANC = _num(labs.get("ANC"))
    PLT = _num(labs.get("PLT")); UA  = _num(labs.get("UA"))

    # 고정 5개 권장 리스트 (요청안 반영)
    if Alb is not None and Alb < 3.5:
        L.append(f"알부민 낮음 → 권장: {_foods(['달걀','연두부','흰살 생선','닭가슴살','귀리죽'])}")
    if K is not None and K < 3.5:
        L.append(f"칼륨 낮음 → 권장: {_foods(['바나나','감자','호박죽','고구마','오렌지'])}")
    if Hb is not None and Hb < 10:
        L.append(f"Hb 낮음(빈혈) → 권장: {_foods(['소고기','시금치','두부','달걀 노른자','렌틸콩'])}")
    if Na is not None and Na < 135:
        L.append(f"나트륨 낮음 → 권장: {_foods(['전해질 음료','미역국','바나나','오트밀죽','삶은 감자'])}")
    if Ca is not None and Ca < 8.5:
        L.append(f"칼슘 낮음 → 권장: {_foods(['연어통조림','두부','케일','브로콜리','(참깨 제외)'])}")
    if Glu is not None and Glu >= 140:
        L.append(f"혈당 높음 → 권장: {_foods(['현미/귀리','두부 샐러드','채소 수프','닭가슴살','사과(소과)'])} · 주의: 당분 많은 간식/음료 피하기")
    if (Cr is not None and Cr > 1.2) or (BUN is not None and BUN > 20):
        L.append(f"신장 수치 상승 → 권장: {_foods(['물/보리차 조금씩 자주','애호박/오이 수프','양배추찜','흰쌀죽','배/사과(소량)'])} · 주의: 단백질 과다·짠 음식 회피, 탈수 주의")
    if (AST is not None and AST >= 50) or (ALT is not None and ALT >= 55):
        L.append(f"간수치 상승(AST/ALT) → 권장: {_foods(['구운 흰살생선','두부','삶은 야채','현미죽(소량)','올리브오일 샐러드'])} · 주의: 기름진/튀김/술 피하기")
    if UA is not None and UA > 7:
        L.append(f"요산 높음 → 권장: {_foods(['우유/요거트','달걀','감자','채소류','체리 등 과일'])} · 주의: 내장/멸치/맥주 등 퓨린 많은 음식 제한")
    if CRP is not None and CRP >= 3:
        L.append(f"CRP 상승(염증) → 권장: {_foods(['토마토','브로콜리','블루베리','연어(완전 익히기)','올리브오일'])} · 주의: 생식 금지, 수분 충분히")

    # ANC 단계별 가이드
    if ANC is not None:
        if ANC < 500:
            L.append("ANC < 500: 생채소 금지 · 모든 음식 완전가열 또는 전자레인지 30초↑ · 멸균/살균 식품 권장 · 조리 후 2시간 지난 음식은 폐기 · 껍질 과일은 **주치의 상담 후**")
            L.append(f"권장: {_foods(['흰죽','계란찜(완숙)','연두부','잘 익힌 고기/생선','통조림 과일(시럽 제거)'])}")
        elif ANC < 1000:
            L.append("ANC 500–1000: 외식은 신선식품 피하고, 조리 완료 후 **바로 섭취** · 손위생 강화")
        else:
            L.append("ANC ≥ 1000: 일반 식이 가능(위생수칙 준수). 생식은 가급적 피하고 익히는 것을 권장")

    if PLT is not None and PLT < 20000:
        L.append(f"혈소판 낮음(PLT<20k) → 권장: {_foods(['계란찜','두부','바나나','오트밀죽','미역국'])} · 주의: 딱딱/자극 음식·술 피하고, 부드러운 칫솔 사용")

    # 혈액암 플래그 시 보충제 경고
    if heme_flag:
        L.append("주의: **철분제+비타민C** 동시 복용 시 흡수 증가. 항암 치료 중/백혈병 환자는 반드시 **주치의와 상담 후** 복용 결정.")

    return L

def _num(x) -> Optional[float]:
    try:
        if x is None: return None
        s = str(x).strip().replace(",", "")
        if s=="": return None
        return float(s)
    except Exception:
        return None
