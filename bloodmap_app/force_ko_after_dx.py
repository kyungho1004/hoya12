    # ▼▼▼ 붙여넣기 위치: 암 모드에서 dx 선택 직후 (들여쓰기 4칸) ▼▼▼
    # 한글 병기 강제 표기 (드롭다운이 영어만 떠도 아래 라벨은 반드시 한글 병기 표시)
    def _is_korean(s): 
        return any('\uac00' <= ch <= '\ud7a3' for ch in (s or ''))
    def _norm(s):
        s = (s or '').strip()
        return s.upper().replace(' ', '')
    DX_KO_LOCAL = {
        'APL':'급성 전골수구성 백혈병','AML':'급성 골수성 백혈병','ALL':'급성 림프구성 백혈병',
        'CML':'만성 골수성 백혈병','CLL':'만성 림프구성 백혈병','PCNSL':'원발성 중추신경계 림프종',
        'DLBCL':'미만성 거대 B세포 림프종','B거대세포종':'미만성 거대 B세포 림프종','B 거대세포종':'미만성 거대 B세포 림프종',
        'B거대세포 림프종':'미만성 거대 B세포 림프종','b거대세포종':'미만성 거대 B세포 림프종',
        'PMBCL':'원발성 종격동 B세포 림프종','HGBL':'고등급 B세포 림프종','BL':'버킷 림프종','FL':'여포성 림프종',
        'MZL':'변연부 림프종','MALT lymphoma':'점막연관 변연부 B세포 림프종','MCL':'외투세포 림프종',
        'cHL':'고전적 호지킨 림프종','NLPHL':'결절성 림프구우세 호지킨 림프종','PTCL-NOS':'말초 T세포 림프종 (NOS)',
        'AITL':'혈관면역모세포성 T세포 림프종','ALCL (ALK+)':'역형성 대세포 림프종 (ALK 양성)','ALCL (ALK−)':'역형성 대세포 림프종 (ALK 음성)',
        'OSTEOSARCOMA':'골육종','EWING SARCOMA':'유잉육종','RHABDOMYOSARCOMA':'횡문근육종','SYNOVIAL SARCOMA':'활막육종',
        'LEIOMYOSARCOMA':'평활근육종','LIPOSARCOMA':'지방육종','UPS':'미분화 다형성 육종','ANGIOSARCOMA':'혈관육종',
        'MPNST':'악성 말초신경초종','DFSP':'피부섬유종증성 육종(DFSP)','CLEAR CELL SARCOMA':'투명세포 육종','EPITHELIOID SARCOMA':'상피양 육종',
        '폐선암':'폐선암','유방암':'유방암','대장암':'결장/직장 선암','위암':'위선암','간세포암':'간세포암(HCC)','췌장암':'췌장암',
        '난소암':'난소암','자궁경부암':'자궁경부암','방광암':'방광암','식도암':'식도암','GIST':'위장관기저종양','NET':'신경내분비종양','MTC':'수질성 갑상선암',
    }
    if dx:
        if _is_korean(dx):
            shown = dx
        else:
            shown = f"{dx} (" + (DX_KO_LOCAL.get(_norm(dx)) or DX_KO_LOCAL.get(dx, '병기 없음')) + ")"
        st.markdown(f"**진단:** {group} - {shown}")
    # ▲▲▲ 여기까지 붙여넣기 ▲▲▲
