# -*- coding: utf-8 -*-
"""Report builders (md/txt/pdf skeleton)."""
from typing import List, Tuple
import datetime as _dt

FOOTER = (
    "\n\n---\n"
    "본 자료는 보호자의 이해를 돕기 위한 참고용 정보이며, "
    "모든 의학적 판단은 주치의 및 의료진의 판단을 따릅니다.\n"
    "제작: Hoya/GPT (자문: Hoya/GPT)\n"
)

def build_markdown_report(nickname_pin: str, items: List[Tuple[str, float, str, str]]):
    t = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# 피수치 해석 결과 ({t})", f"- 사용자: `{nickname_pin}`", ""]
    for (k,v,level,hint) in items:
        lines.append(f"- **{k}**: {v} → {level} · {hint}")
    lines.append(FOOTER)
    return "\n".join(lines)

def to_txt(md_text: str) -> str:
    return md_text.replace("# ", "").replace("**", "")

# (PDF 생성은 reportlab 세팅이 필요하므로 앱 쪽에서 구현/호출하도록 남겨둠)
