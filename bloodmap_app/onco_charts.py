# -*- coding: utf-8 -*-
from __future__ import annotations
import io
from typing import List, Optional, Dict
from datetime import date
import pandas as pd

try:
    import streamlit as st  # type: ignore
except Exception:
    class _Dummy:
        def __getattr__(self, k): return lambda *a, **k: None
    st = _Dummy()  # type: ignore

def _init_logs() -> pd.DataFrame:
    cols = ["Date","WBC","ANC","Hb","PLT","CRP"]
    df = st.session_state.get("onco_logs")
    if df is None:
        df = pd.DataFrame(columns=cols)
        st.session_state["onco_logs"] = df
    else:
        # Normalize cols if loaded
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df = df[cols]
    return df

def _trend_arrow(series: pd.Series) -> str:
    s = pd.to_numeric(series.dropna(), errors="coerce")
    if len(s) < 2: 
        return "→"
    last = s.iloc[-1]
    prev = s.iloc[-2]
    if pd.isna(last) or pd.isna(prev):
        return "→"
    if last > prev * 1.05: return "↑"
    if last < prev * 0.95: return "↓"
    return "→"

def _apply_window(df: pd.DataFrame, window: str) -> pd.DataFrame:
    if df.empty: return df
    df2 = df.copy()
    df2["Date"] = pd.to_datetime(df2["Date"])
    df2.sort_values("Date", inplace=True)
    if window == "7일":
        return df2.tail(7)
    if window == "30일":
        return df2.tail(30)
    if window == "90일":
        return df2.tail(90)
    return df2

def _apply_smooth(s: pd.Series, mode: str) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if mode == "EMA":
        return s.ewm(alpha=0.3, adjust=False).mean()
    if mode == "MA(3)":
        return s.rolling(window=3, min_periods=1).mean()
    return s

def _maybe_log10(s: pd.Series, use_log: bool) -> pd.Series:
    if not use_log:
        return s
    s = pd.to_numeric(s, errors="coerce")
    return (s.where(s>0)).apply(lambda x: None if pd.isna(x) else (0 if x<=0 else __import__("math").log10(x)))

def _chart(df: pd.DataFrame, ycol: str, title: str, log_toggle: bool, smooth_mode: str):
    if df.empty:
        st.caption("데이터가 없습니다.")
        return
    y = _apply_smooth(df[ycol], smooth_mode)
    if ycol in ("WBC","CRP"):
        y = _maybe_log10(y, log_toggle)
        unit = "(log10)" if log_toggle else ""
    else:
        unit = ""
    plot_df = pd.DataFrame({"Date": df["Date"], ycol: y})
    plot_df = plot_df.set_index("Date")
    st.write(f"**{title}** {unit} { _trend_arrow(y) }")
    st.line_chart(plot_df, use_container_width=True)

def ui_onco_trends_card(key: str = "onco") -> pd.DataFrame:
    st.markdown("### 📊 암환자 피수치 추적")
    df = _init_logs()

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: d = st.date_input("날짜", value=date.today(), key=f"{key}_d")
    with c2: wbc = st.number_input("WBC (10^3/µL)", min_value=0.0, step=0.1, key=f"{key}_wbc")
    with c3: anc = st.number_input("ANC (/µL)", min_value=0.0, step=100.0, key=f"{key}_anc")
    with c4: hb  = st.number_input("Hb (g/dL)", min_value=0.0, step=0.1, key=f"{key}_hb")
    with c5: plt = st.number_input("PLT (10^3/µL)", min_value=0.0, step=1.0, key=f"{key}_plt")
    with c6: crp = st.number_input("CRP (mg/L)", min_value=0.0, step=0.1, key=f"{key}_crp")

    cA, cB, cC, cD = st.columns(4)
    with cA: window = st.selectbox("보기", ["7일","30일","90일","전체"], index=1, key=f"{key}_win")
    with cB: smooth = st.selectbox("스무딩", ["없음","MA(3)","EMA"], index=0, key=f"{key}_smooth")
    with cC: log_wbc = st.checkbox("WBC log10", value=True, key=f"{key}_log_wbc")
    with cD: log_crp = st.checkbox("CRP log10", value=False, key=f"{key}_log_crp")

    btn1, btn2, btn3 = st.columns(3)
    if btn1.button("오늘 기록 추가/수정", key=f"{key}_add"):
        row = {"Date": d.strftime("%Y-%m-%d"), "WBC": wbc, "ANC": anc, "Hb": hb, "PLT": plt, "CRP": crp}
        if df.empty:
            df2 = pd.DataFrame([row])
        else:
            df2 = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df2 = df2.drop_duplicates(subset=["Date"], keep="last")
        st.session_state["onco_logs"] = df2
        st.success("기록 저장됨")
    if btn2.button("CSV 내보내기", key=f"{key}_exp"):
        exp = st.session_state.get("onco_logs", pd.DataFrame()).to_csv(index=False)
        st.download_button("⬇️ onco_logs.csv", data=exp, file_name="onco_logs.csv")
    if btn3.button("CSV 가져오기", key=f"{key}_imp"):
        up = st.file_uploader("onco_logs.csv 업로드", type=["csv"], key=f"{key}_upl")
        if up is not None:
            try:
                dfu = pd.read_csv(up)
                st.session_state["onco_logs"] = dfu
                st.success("불러오기 완료")
            except Exception as e:
                st.error(f"가져오기 실패: {e}")

    df = st.session_state.get("onco_logs", pd.DataFrame())
    df = _apply_window(df, window)

    # Charts (one per metric; mobile-friendly)
    _chart(df, "WBC", "WBC (10^3/µL)", log_wbc, smooth)
    _chart(df, "ANC", "ANC (/µL)", False, smooth)
    _chart(df, "Hb",  "Hemoglobin (g/dL)", False, smooth)
    _chart(df, "PLT", "Platelet (10^3/µL)", False, smooth)
    _chart(df, "CRP", "CRP (mg/L)", log_crp, smooth)

    st.caption("※ 참고선(텍스트): ANC<500 심한 호중구감소, PLT<10 주사 필요 가능, Hb<7 수혈 고려 등 — 병원 지침 우선.")
    return df
