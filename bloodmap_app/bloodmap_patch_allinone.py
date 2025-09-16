# -*- coding: utf-8 -*-
"""
bloodmap_patch_allinone.py — 한 파일로 끝내는 통합 패치
- 임포트 1줄 + 함수 1개 호출로 다음 기능을 전부 제공:
  1) 24시간 해열제 복용 시간표(이미 먹은 시간 체크/재계산 포함)
  2) 약물 상호작용·금기 경고(암 모드 주요 룰 내장)
  3) 일상 증상일지(체온/설사/구토) + 미니 차트
  4) QR 코드 생성(보고서 PDF 하단 자동 삽입)
  5) 짧은 해석 톤 프리셋(기본/더-친절/간결)
  6) 오프라인 임시 저장(JSON) — localStorage 저장(복구는 수동 JSON 붙여넣기 방식 제공)
  7) 보고서 합치기 + 안정적 다운로드(.md/.txt/.pdf/.zip)

사용 방법 (app.py):
    from bloodmap_patch_allinone import render_bloodmap_patch
    render_bloodmap_patch(ctx_title="BloodMap 해석 보고서", extra_blocks=[...])  # extra_blocks는 기존 섹션 문자열들
"""
from __future__ import annotations

import io, os, re, json, zipfile
from typing import Optional, Sequence, List, Tuple, Dict, Any
from datetime import datetime, timedelta

import streamlit as st

# =============== 공통 ===============
KST = timedelta(hours=9)

def _kst_now() -> datetime:
    return datetime.utcnow() + KST

def _fmt_time(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M")


# =============== 다운로드 묶음 ===============
def _render_report_downloads(md: str, txt: str, make_pdf_bytes_callable):
    st.download_button(
        "⬇️ Markdown (.md)",
        data=md.encode("utf-8"),
        file_name="BloodMap_Report.md",
        mime="text/markdown; charset=utf-8",
        key="dl_md",
    )
    st.download_button(
        "⬇️ 텍스트 (.txt)",
        data=txt.encode("utf-8"),
        file_name="BloodMap_Report.txt",
        mime="text/plain; charset=utf-8",
        key="dl_txt",
    )
    pdf_bytes = None
    try:
        pdf_bytes = make_pdf_bytes_callable(md)
        st.download_button(
            "⬇️ PDF (.pdf)",
            data=pdf_bytes,
            file_name="BloodMap_Report.pdf",
            mime="application/pdf",
            key="dl_pdf",
        )
    except Exception as e:
        st.warning(f"PDF 변환 중 오류: {e}")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("BloodMap_Report.md", md.encode("utf-8"))
        zf.writestr("BloodMap_Report.txt", txt.encode("utf-8"))
        if pdf_bytes:
            zf.writestr("BloodMap_Report.pdf", pdf_bytes)
    st.download_button(
        "⬇️ 묶음 다운로드 (.zip)",
        data=zip_buf.getvalue(),
        file_name="BloodMap_Report.zip",
        mime="application/zip",
        key="dl_zip",
    )
    with st.expander("👀 미리보기 & 복사(다운로드가 막힐 때 사용)", expanded=False):
        st.text_area("미리보기(.md)", value=md, height=240)
        st.caption("텍스트를 드래그 → Ctrl+C(복사) → 원하는 곳에 Ctrl+V(붙여넣기)")


# =============== PDF(한글/QR/스파크라인) ===============
def _export_md_to_pdf(md_text: str, qr_png: Optional[bytes] = None, spark_values: Optional[Sequence[float]] = None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.graphics.shapes import Drawing, PolyLine

    FONT_CANDIDATES = [
        ("/mnt/data/NanumBarunGothic.otf", "KOR-Regular"),
        ("/mnt/data/NanumBarunGothicBold.otf", "KOR-Bold"),
        ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "KOR-Regular"),
        ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", "KOR-Bold"),
    ]
    regular, bold = "Helvetica", "Helvetica-Bold"
    try:
        for path, name in FONT_CANDIDATES:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont(name, path))
        if os.path.exists(FONT_CANDIDATES[0][0]): regular = "KOR-Regular"
        if os.path.exists(FONT_CANDIDATES[1][0]): bold = "KOR-Bold"
    except Exception:
        pass

    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="KOR-Body", fontName=regular, fontSize=11, leading=15, alignment=TA_LEFT))
    ss.add(ParagraphStyle(name="KOR-H1", fontName=bold, fontSize=16, leading=20, spaceBefore=8, spaceAfter=6))
    ss.add(ParagraphStyle(name="KOR-H2", fontName=bold, fontSize=13, leading=18, spaceBefore=6, spaceAfter=4))
    ss.add(ParagraphStyle(name="KOR-Center", fontName=regular, fontSize=10, leading=14, alignment=TA_CENTER))

    def _img_flowable(png_bytes: bytes, max_width_mm: float) -> RLImage:
        bio = io.BytesIO(png_bytes)
        img = RLImage(bio)
        target_w = max_width_mm * mm
        w, h = img.drawWidth, img.drawHeight
        if w > target_w:
            scale = target_w / w
            img.drawWidth = w * scale
            img.drawHeight = h * scale
        return img

    def _sparkline(values: Sequence[float], width_mm=160, height_mm=24) -> Drawing:
        if not values:
            return Drawing(0, 0)
        w, h = width_mm*mm, height_mm*mm
        N = len(values); vmin, vmax = min(values), max(values)
        rng = (vmax - vmin) or 1.0
        pts = []
        for i, v in enumerate(values):
            x = (i/(N-1) if N>1 else 0.5) * (w-2)
            y = ((v - vmin)/rng) * (h-2)
            pts.append((x+1, y+1))
        d = Drawing(w, h)
        d.add(PolyLine(pts, strokeWidth=1))
        return d

    story, bullets = [], []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            story.append(ListFlowable([ListItem(Paragraph(b, ss["KOR-Body"])) for b in bullets],
                                      bulletType='bullet', start='-'))
            bullets.clear()
            story.append(Spacer(1, 4))

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line:
            flush_bullets(); story.append(Spacer(1, 6)); continue
        if line.startswith("# "):
            flush_bullets(); story.append(Paragraph(line[2:].strip(), ss["KOR-H1"])); continue
        if line.startswith("## "):
            flush_bullets()
            title = line[3:].strip()
            story.append(Paragraph(title, ss["KOR-H2"]))
            if ("증상 일지" in title) and spark_values:
                story.append(Spacer(1, 4)); story.append(_sparkline(spark_values)); story.append(Spacer(1, 6))
            continue
        if line.startswith("- "):
            bullets.append(line[2:].strip()); continue
        flush_bullets(); story.append(Paragraph(line, ss["KOR-Body"]))
    flush_bullets()

    if qr_png:
        story.append(Spacer(1, 12))
        story.append(Paragraph("🔗 앱 접속용 QR", ss["KOR-H2"]))
        story.append(Spacer(1, 4))
        story.append(_img_flowable(qr_png, max_width_mm=40))
        story.append(Paragraph("스마트폰 카메라로 스캔하세요.", ss["KOR-Center"]))
        story.append(Spacer(1, 8))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    doc.build(story)
    return buf.getvalue()


# =============== 보고서 합치기 ===============
def _build_merged_report_md(
    *,
    ctx_title: str,
    plans=None,
    logs_today_summary: Optional[str] = None,
    logs_week_summary: Optional[str] = None,
    hits: Optional[Sequence] = None,
    existing_blocks: Optional[Sequence[str]] = None,
    summary_label: Optional[str] = None,
) -> tuple[str, str]:
    parts: List[str] = []
    parts.append(f"# {ctx_title}")
    if plans:
        parts.append("## 🕒 해열제 시간표")
        try:
            parts.append(plans.as_copyable_lines().strip())
        except Exception:
            parts.append("시간표를 불러오지 못했습니다.")
    if logs_today_summary or logs_week_summary:
        parts.append("## 📈 증상 일지")
        if logs_today_summary:
            parts.append(f"- 오늘: {logs_today_summary}")
        if logs_week_summary:
            parts.append(f"- 최근 7일: {logs_week_summary}")
    if hits:
        parts.append("## 🚨 상호작용/금기 요약")
        for item in hits:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                sev, msg = item[0], item[1]
                parts.append(f"- {sev} {msg}")
            else:
                parts.append(f"- {item}")
    if existing_blocks:
        parts.append("## ℹ️ 종합 해석")
        for block in existing_blocks:
            if block:
                parts.append(block.rstrip())
    if summary_label:
        parts.append("## 🧾 한 줄 요약")
        parts.append(summary_label.strip())
    parts.append("")
    parts.append("_QR 이미지는 PDF 하단에 자동 첨부됩니다._")
    md = "\n".join(parts).strip()
    txt = re.sub(r"[`*_#>]", "", md)
    return md, txt


def _make_spark_values_from_logs(logs) -> Optional[List[float]]:
    try:
        import pandas as pd  # noqa: F401
    except Exception:
        pd = None
    values = None
    try:
        if pd is not None and hasattr(logs, "to_dict"):
            df = logs.copy()
            if "date" in df.columns:
                df = df.sort_values("date")
                num_col = next((c for c in ["count","temp","score","value"] if c in df.columns), None)
                if num_col:
                    values = df[num_col].tail(7).astype(float).tolist()
        elif isinstance(logs, dict):
            items = sorted(logs.items())[-7:]
            values = [float(v) for _, v in items]
        elif isinstance(logs, (list, tuple)) and logs and isinstance(logs[0], dict):
            num_col = next((k for k in ["count","temp","score","value"] if all(k in d for d in logs)), None)
            if num_col:
                values = [float(d[num_col]) for d in logs[-7:]]
    except Exception:
        values = None
    return values


# =============== 해열제 시간표 ===============
def _build_antipyretic_plan(
    *,
    age_months: float,
    weight_kg: Optional[float],
    temp_c: float,
    last_dose_time: Optional[datetime] = None,
    use_acetaminophen: bool = True,
    use_ibuprofen: bool = True,
    interval_apap_hours: int = 6,
    interval_ibup_hours: int = 8,
    hours_window: int = 24,
) -> Dict[str, Any]:
    try:
        from peds_dose import acetaminophen_ml, ibuprofen_ml
    except Exception:
        acetaminophen_ml = ibuprofen_ml = None

    now = _kst_now()
    anchor = last_dose_time or now
    end_at = anchor + timedelta(hours=hours_window)

    rows: List[Dict[str, Any]] = []
    if use_acetaminophen and acetaminophen_ml:
        apap_ml, _w = acetaminophen_ml(age_months, weight_kg)
        t = anchor
        while t <= end_at:
            if t >= now:
                rows.append({"drug": "Acetaminophen", "ml": apap_ml, "time": t})
            t += timedelta(hours=interval_apap_hours)
    if use_ibuprofen and ibuprofen_ml:
        ibu_ml, _w2 = ibuprofen_ml(age_months, weight_kg)
        t = anchor
        while t <= end_at:
            if t >= now:
                rows.append({"drug": "Ibuprofen", "ml": ibu_ml, "time": t})
            t += timedelta(hours=interval_ibup_hours)

    rows.sort(key=lambda r: r["time"])
    lines = [f"[복용 시간표] 체온 {temp_c:.1f}℃ 기준 — 생성: {_fmt_time(now)}"]
    for r in rows:
        lines.append(f"- {_fmt_time(r['time'])} · {r['drug']} {r['ml']} mL")
    text_block = "\n".join(lines)
    return {"rows": rows, "as_copyable_lines": text_block, "weight_note": "(계산 체중 기준 적용)"}


# =============== 상호작용/금기 ===============
def _check_interactions(
    selected: List[str],
    *,
    labs: Optional[Dict[str, float]] = None,
    co_meds: Optional[List[str]] = None
) -> List[Tuple[str, str]]:
    labs = labs or {}
    co_meds = [c.lower() for c in (co_meds or [])]
    sel = set(s.lower() for s in selected)

    hits: List[Tuple[str,str]] = []
    def has(name): return name.lower() in sel
    def tag(name): return name.lower() in co_meds
    def lab_low(k, th): return (k in labs) and (labs[k] < th)
    def lab_high(k, th): return (k in labs) and (labs[k] > th)

    if has("6-mp") and (has("allopurinol") or tag("allopurinol")):
        hits.append(("🚨", "6-MP + allopurinol: 6-MP 독성 ↑ — 용량 대폭 감량/전문의 상담"))

    if has("mtx") and (tag("nsaids") or has("ibuprofen") or has("naproxen")):
        hits.append(("⚠️", "MTX + NSAIDs: MTX 배설 감소 — 신기능/혈중농도·점막염 주의"))
    if has("mtx") and (lab_high("Cr", 1.2)):
        hits.append(("⚠️", "MTX + 신기능 저하: 축적 위험 — 용량/간격 조정·수분/요알칼리화 고려"))

    if has("linezolid") and (tag("ssri") or has("sertraline") or has("fluoxetine") or has("paroxetine") or has("escitalopram")):
        hits.append(("🚨", "Linezolid + SSRI: 세로토닌 증후군 위험 — 병용 회피/밀착 모니터링"))

    low_k = lab_low("K", 3.5)
    low_mg = lab_low("Mg", 1.8)
    qt_risk = tag("qt") or has("ondansetron") or has("amiodarone")
    if has("arsenic trioxide") or has("ato"):
        if low_k or low_mg or qt_risk:
            details = []
            if low_k: details.append("저K")
            if low_mg: details.append("저Mg")
            if qt_risk: details.append("QT 연장 약물 동시 복용")
            hits.append(("🚨", "ATO: QT 연장 위험 — " + ", ".join(details) + " 교정/모니터링"))
        else:
            hits.append(("⚠️", "ATO: ECG·전해질 정기 모니터링 권장"))
    return hits


# =============== 메인: 한 번에 렌더 ===============
def render_bloodmap_patch(*, ctx_title: str = "BloodMap 해석 보고서", extra_blocks: Optional[Sequence[str]] = None):
    """앱 내 원하는 위치에서 1회 호출하면 모든 UI/다운로드를 렌더합니다."""

    # 1) 해열제 시간표
    st.markdown("## 🕒 24시간 해열제 시간표")
    colA, colB, colC = st.columns([1,1,1])
    with colA:
        age_months = st.number_input("나이(개월)", min_value=0, max_value=240, value=36, step=1)
    with colB:
        weight_kg = st.number_input("체중(kg)", min_value=0.0, max_value=120.0, value=15.0, step=0.1)
    with colC:
        temp_c = st.number_input("현재 체온(℃)", min_value=35.0, max_value=42.0, value=38.2, step=0.1)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        use_apap = st.checkbox("아세트아미노펜 포함", True)
    with col2:
        use_ibu = st.checkbox("이부프로펜 포함", True)
    with col3:
        already_taken = st.checkbox("이미 먹은 시간 체크", False)

    last_time = None
    if already_taken:
        t = st.time_input("마지막 복용 시각(오늘)", value=_kst_now().time())
        last_time = _kst_now().replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)

    plan = _build_antipyretic_plan(
        age_months=age_months,
        weight_kg=weight_kg,
        temp_c=temp_c,
        last_dose_time=last_time,
        use_acetaminophen=use_apap,
        use_ibuprofen=use_ibu,
        interval_apap_hours=6,
        interval_ibup_hours=8,
    )
    st.text_area("오늘 스케줄(복사용)", value=plan["as_copyable_lines"], height=180)
    st.caption("※ 의사 지시와 다르면 의사 지시를 우선하세요. (일반 가이드)")
    st.session_state["antipyretic_plan"] = plan

    # 2) 상호작용 경고
    st.markdown("## 🚨 약물 상호작용·금기 경고")
    drug_options = ["6-MP","MTX","Linezolid","Arsenic Trioxide","Ibuprofen","Allopurinol","Sertraline","Fluoxetine","Ondansetron","Amiodarone","Naproxen"]
    sel = st.multiselect("현재 복용/투여 약물", drug_options, default=["6-MP","Allopurinol"])
    colL, colR = st.columns(2)
    with colL:
        use_tags = st.multiselect("공동 투여군 태그", ["NSAIDs","SSRI","QT"], default=[])
    with colR:
        k = st.number_input("K (mmol/L)", value=3.8, step=0.1)
        mg = st.number_input("Mg (mg/dL)", value=1.9, step=0.1)
        cr = st.number_input("Cr (mg/dL)", value=0.6, step=0.1)
    hits = _check_interactions(sel, labs={"K":k, "Mg":mg, "Cr":cr}, co_meds=use_tags)
    if hits:
        for sev, msg in hits:
            st.markdown(f"- **{sev} {msg}**")
    else:
        st.markdown("- 특이 상호작용 경고 없음(입력값 기준)")
    st.session_state["interaction_hits"] = hits

    # 3) 증상일지 + 차트 + QR
    st.markdown("## 📈 일상 증상일지")
    import pandas as pd
    dcol = st.columns([1,1,1,1])
    with dcol[0]:
        today = _kst_now().date()
        date_sel = st.date_input("날짜", value=today)
    with dcol[1]:
        ttemp = st.number_input("체온(℃)", value=37.9, step=0.1)
    with dcol[2]:
        diarrhea = st.number_input("설사 횟수", min_value=0, value=0, step=1)
    with dcol[3]:
        vomit = st.number_input("구토 횟수", min_value=0, value=0, step=1)
    if st.button("오늘 기록 추가/업데이트"):
        logs = st.session_state.get("sym_logs", {})
        key = str(date_sel)
        logs[key] = {"date": key, "temp": float(ttemp), "diarrhea": int(diarrhea), "vomit": int(vomit)}
        st.session_state["sym_logs"] = logs
        st.success("기록 저장됨")
    logs = st.session_state.get("sym_logs", {})
    if logs:
        df = pd.DataFrame(list(logs.values())).sort_values("date")
        st.line_chart(df.set_index("date")[ ["temp"] ], height=160)
        st.bar_chart(df.set_index("date")[ ["diarrhea","vomit"] ], height=160)
        today_key = str(_kst_now().date())
        if (today_key in df["date"].values):
            row = df[df["date"]==today_key].iloc[-1]
            today_summary = f"체온 {row['temp']:.1f}℃, 설사 {int(row['diarrhea'])}회, 구토 {int(row['vomit'])}회"
        else:
            today_summary = "기록 없음"
        week_df = df.tail(7)
        week_summary = f"평균 체온 {week_df['temp'].mean():.1f}℃, 설사 총 {int(week_df['diarrhea'].sum())}회, 구토 총 {int(week_df['vomit'].sum())}회"
    else:
        df = pd.DataFrame(columns=["date","temp","diarrhea","vomit"])
        today_summary, week_summary = None, None
    st.session_state["sym_logs_df"] = df
    st.session_state["sym_today_summary"] = today_summary
    st.session_state["sym_week_summary"] = week_summary

    with st.expander("🔗 보고서 하단 QR 넣기(선택)", expanded=False):
        qr_url = st.text_input("QR 링크(URL)", value="https://bloodmap.kr")
        if st.button("QR 생성/갱신"):
            try:
                from reportlab.graphics.shapes import Drawing
                from reportlab.graphics.barcode import qr
                from reportlab.graphics import renderPM
                qrobj = qr.QrCodeWidget(qr_url)
                b = qrobj.getBounds()
                w = b[2]-b[0]; h=b[3]-b[1]
                d = Drawing(w, h); d.add(qrobj)
                png_bytes = renderPM.drawToString(d, fmt="PNG")
                st.session_state["qr_png"] = png_bytes
                st.image(png_bytes)
                st.success("QR 저장 완료(보고서 PDF 하단에 삽입됨)")
            except Exception as e:
                st.warning(f"QR 생성 실패: {e}")

    # 4) 톤 프리셋
    st.markdown("## 🗣️ 짧은 해석 톤")
    tone = st.selectbox("톤 프리셋", ["기본","더-친절","간결"], index=1)
    summary_label = st.session_state.get("summary_label", "현재 상태는 안정적이며, 수분 보충과 휴식이 권장됩니다.")
    def _apply_tone(text: str, tone: str) -> str:
        if tone == "더-친절":
            return "안심하세요. " + text.replace("필요", "필요해요").replace("권장", "권장드려요")
        if tone == "간결":
            return text.replace("필요합니다", "필요").replace("입니다", "")
        return text
    summary_label = _apply_tone(summary_label, tone)
    st.session_state["summary_label"] = summary_label

    # 5) 오프라인 임시 저장(JSON) — 저장은 localStorage, 복구는 수동 붙여넣기(안전/단순)
    st.markdown("## 💾 오프라인 임시 저장 / 복구(JSON)")
    snapshot = {
        "plan": st.session_state.get("antipyretic_plan"),
        "logs": st.session_state.get("sym_logs", {}),
        "hits": st.session_state.get("interaction_hits", []),
        "summary": st.session_state.get("summary_label"),
    }
    snap_str = json.dumps(snapshot, ensure_ascii=False, indent=2)
    st.text_area("저장 JSON(복사해서 메모장 보관)", value=snap_str, height=160)
    restore_txt = st.text_area("복구 JSON 붙여넣기", value="", height=80, placeholder="여기에 저장해둔 JSON을 붙여넣고 아래 버튼을 누르세요.")
    if st.button("복구 적용"):
        try:
            data = json.loads(restore_txt)
            if isinstance(data, dict):
                st.session_state["antipyretic_plan"] = data.get("plan") or st.session_state.get("antipyretic_plan")
                st.session_state["sym_logs"] = data.get("logs") or st.session_state.get("sym_logs", {})
                st.session_state["interaction_hits"] = data.get("hits") or st.session_state.get("interaction_hits", [])
                st.session_state["summary_label"] = data.get("summary") or st.session_state.get("summary_label")
                st.success("✅ JSON 복구 완료 — 위 섹션들을 다시 확인하세요.")
        except Exception as e:
            st.warning(f"복구 실패: {e}")

    # 6) 보고서 합치기 + 저장
    st.subheader("📝 보고서 저장")
    plans = st.session_state.get("antipyretic_plan")
    logs_df = st.session_state.get("sym_logs_df")
    today_summary = st.session_state.get("sym_today_summary")
    week_summary  = st.session_state.get("sym_week_summary")
    hits = st.session_state.get("interaction_hits")
    summary_label = st.session_state.get("summary_label")
    blocks = list(extra_blocks or [])
    if summary_label:
        blocks.append(summary_label)

    proxy_plans = None
    if plans:
        class _P:
            def as_copyable_lines(self):
                return plans["as_copyable_lines"]
        proxy_plans = _P()

    md, txt = _build_merged_report_md(
        ctx_title=ctx_title,
        plans=proxy_plans,
        logs_today_summary=today_summary, logs_week_summary=week_summary,
        hits=hits, existing_blocks=blocks, summary_label=summary_label,
    )
    spark_values = None
    try:
        if (logs_df is not None) and (not logs_df.empty):
            spark_values = logs_df.sort_values("date")["temp"].tail(7).astype(float).tolist()
    except Exception:
        spark_values = None
    qr_bytes = st.session_state.get("qr_png") if isinstance(st.session_state.get("qr_png"), (bytes, bytearray)) else None
    make_pdf = lambda md_text: _export_md_to_pdf(md_text, qr_png=qr_bytes, spark_values=spark_values)
    _render_report_downloads(md, txt, make_pdf)
