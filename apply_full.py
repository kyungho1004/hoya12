# -*- coding: utf-8 -*-
# apply_full_patch.py
# Idempotent patcher to wire:
# - graph_store, carelog_ext, csv_importer, unit_guard, er_onepage
import sys, re
from pathlib import Path

APP = Path(sys.argv[1] if len(sys.argv)>1 else "app.py").read_text(encoding="utf-8", errors="ignore")

def once_insert(code: str, marker: str, payload: str, where="after"):
    if payload.strip() in code:
        return code
    i = code.find(marker)
    if i == -1: 
        return code
    return (code[:i+len(marker)] + payload + code[i+len(marker):]) if where=="after" else (code[:i] + payload + code[i:])

# 0) import wiring
imp_marker = "from zoneinfo import ZoneInfo"
imp_payload = "\\nfrom graph_store import save_config, save_labs_csv, load_config, exists as graph_exists\\nfrom carelog_ext import add as care_add, read as care_read, delete_last as care_del, export_txt as care_txt, export_ics as care_ics\\nfrom csv_importer import sniff_and_parse\\nfrom unit_guard import unit_guard\\nfrom er_onepage import render_er_md\\n"
APP = APP.replace(imp_marker, imp_marker + imp_payload)

# 1) PIN lock on pinned graph (hide unless has_key)
lock_marker = "st.subheader(\"📈 피수치 추세\")"
lock_payload = r"""
        # PIN lock for pinned graph
        if not has_key:
            st.info("별명+PIN 사용자만 고정 그래프를 볼 수 있습니다.")
            show_graph = False
        else:
            show_graph = True
"""
APP = once_insert(APP, lock_marker, lock_payload, "after")

# 2) External graph save/load after we draw or update
save_marker = "st.button(\"그래프 저장\""
if save_marker in APP:
    # append save actions near existing save button
    APP = APP.replace(save_marker, save_marker)  # left as-is
else:
    # Inject a simple save/load row into graph section
    graph_block = r"""
        # 외부 저장/불러오기
        if has_key:
            cols = st.columns(3)
            with cols[0]:
                if st.button("📦 그래프 구성 저장", key="graph_save"):
                    cfg = ctx.get("graph_cfg", {"picked": list(labs.keys()) if isinstance(labs, dict) else []})
                    p = save_config(nick, pin, cfg)
                    st.success(f"저장됨: {p.name}")
                    # also dump labs table (if any) for continuity
                    rows = ctx.get("lab_rows", [])
                    try:
                        save_labs_csv(nick, pin, rows or [])
                    except Exception:
                        pass
            with cols[1]:
                if st.button("📥 불러오기", key="graph_load"):
                    cfg = load_config(nick, pin)
                    if cfg:
                        ctx["graph_cfg"] = cfg
                        st.success("불러왔습니다.")
                    else:
                        st.warning("저장된 구성이 없습니다.")
            with cols[2]:
                st.caption("저장 경로: /mnt/data/bloodmap_graph")
    """
    APP = once_insert(APP, lock_marker, graph_block, "after")

# 3) Care log toggles + add/delete + export (TXT/PDF/ICS)
care_marker = "st.subheader(\"🧒 소아\")"  # fallback anchor; insert near pediatric section footer
care_payload = r"""
        st.markdown("---")
        st.subheader("📝 케어 로그 (암/일상/소아 공통)")
        if not has_key:
            st.info("별명+PIN 설정 후 기록할 수 있습니다.")
        else:
            tab1, tab2, tab3 = st.tabs(["암", "일상", "소아"])
            with tab1:
                c = st.text_input("암 모드 메모/증상", key="care_cancer")
                if st.button("추가(암)", key="care_add_cancer") and c:
                    care_add(nick, pin, "암", c); st.success("추가됨")
            with tab2:
                c = st.text_input("일상 메모/증상", key="care_daily")
                if st.button("추가(일상)", key="care_add_daily") and c:
                    care_add(nick, pin, "일상", c); st.success("추가됨")
            with tab3:
                c = st.text_input("소아 메모/증상", key="care_peds")
                if st.button("추가(소아)", key="care_add_peds") and c:
                    care_add(nick, pin, "소아", c); st.success("추가됨")

            r = care_read(nick, pin, 24)
            if r:
                st.write("최근 24h")
                for x in r[-50:]:
                    st.write(f"- [{x.get('ts_kst','')}] {x.get('type','')}: {x.get('detail','')}")
                cols = st.columns(4)
                with cols[0]:
                    if st.button("↩️ 마지막 삭제", key="care_del_last"):
                        if care_del(nick, pin): st.success("삭제됨")
                        else: st.warning("삭제할 항목이 없습니다.")
                with cols[1]:
                    if st.button("TXT 내보내기", key="care_export_txt"):
                        st.download_button("다운로드", data=care_txt(nick,pin), file_name="carelog_24h.txt", mime="text/plain", key="dl_txt")
                with cols[2]:
                    if st.button("ICS 내보내기", key="care_export_ics"):
                        st.download_button("다운로드", data=care_ics(nick,pin), file_name="carelog_24h.ics", mime="text/calendar", key="dl_ics")
                with cols[3]:
                    if st.button("PDF 내보내기(ER 원페이지)", key="care_export_pdf"):
                        # assemble ER one-page using current context and care log text
                        care_text = care_txt(nick,pin)
                        summary = {"risk": ctx.get("risk","N/A"), "triage": ctx.get("triage","N/A"),
                                   "key_findings": ctx.get("findings",[]), "vitals": ctx.get("vitals_text",""),
                                   "labs_md": ctx.get("labs_md","")}
                        md = render_er_md(summary, care_text)
                        from pdf_export import export_md_to_pdf
                        pdf_bytes = export_md_to_pdf(md)
                        st.download_button("ER_OnePage.pdf 다운로드", data=pdf_bytes, file_name="ER_OnePage.pdf", mime="application/pdf", key="dl_pdf")
            else:
                st.caption("최근 24시간 기록 없음")
"""
APP = once_insert(APP, care_marker, care_payload, "after")

# 4) CSV Import Wizard (Labs)
wizard_anchor = "st.subheader(\"🧪 피수치 입력\")"
wizard_payload = r"""
        with st.expander("🧾 CSV Import Wizard", expanded=False):
            up = st.file_uploader("CSV 업로드(COLUMNS: ts_kst,WBC,Hb,PLT,CRP,ANC,Na,K,Cr)", type=["csv"], key="csv_imp")
            if up is not None:
                try:
                    rows = sniff_and_parse(up.getvalue())
                    st.success(f"{len(rows)}행 불러옴")
                    ctx["lab_rows"] = rows
                except Exception as _e:
                    st.error(f"CSV 파싱 오류: {_e}")
"""
APP = once_insert(APP, wizard_anchor, wizard_payload, "after")

# 5) Unit Guard (show warnings when labs loaded)
guard_marker = "st.subheader(\"🧪 피수치 요약\")"
guard_payload = r"""
        try:
            warns = unit_guard(labs or {})
            for w in warns:
                st.warning("단위 가드: " + w)
        except Exception:
            pass
"""
APP = once_insert(APP, guard_marker, guard_payload, "after")

# 6) Ensure ER export button also appears under results export (best-effort)
export_anchor = "def _export_report("
if export_anchor in APP:
    # Leave function body untouched; ER OnePage is added in care log section above.
    pass

Path("/mnt/data/app_full_patched.py").write_text(APP, encoding="utf-8")
print("app_full_patched.py written")
