# -*- coding: utf-8 -*-
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def _load_user_df(history_csv: str, user_key: str) -> pd.DataFrame:
    if not os.path.exists(history_csv):
        return pd.DataFrame()
    try:
        df = pd.read_csv(history_csv)
    except Exception:
        return pd.DataFrame()
    if "user_key" not in df.columns:
        return pd.DataFrame()
    df = df[df["user_key"] == user_key].copy()
    if df.empty:
        return df
    # Parse timestamp and sort
    if "timestamp" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
        except Exception:
            pass
    return df

def _line(df, x, y, title, ylabel):
    if df.empty or y not in df.columns:
        return
    series = df[[x, y]].dropna()
    if series.empty:
        return
    fig, ax = plt.subplots()
    ax.plot(series[x], series[y], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Date/Time")
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

def render_graphs(history_csv: str, user_key: str):
    """Render WBC, Hb, PLT, ANC, CRP trends for the given user_key."""
    if not user_key:
        st.info("별명과 4자리 PIN을 입력하면 그래프가 활성화됩니다.")
        return
    df = _load_user_df(history_csv, user_key)
    if df.empty or len(df) < 1:
        st.info("아직 저장된 기록이 없습니다. 결과를 저장하면 그래프가 생성됩니다.")
        return
    st.subheader("📈 추이 그래프")
    st.caption("동일한 별명#PIN으로 저장된 기록을 시간순으로 표시합니다.")
    x = "timestamp"
    _line(df, x, "WBC", "WBC 추이 (×10³/µL)", "WBC (×10³/µL)")
    _line(df, x, "Hb", "Hb 추이 (g/dL)", "Hb (g/dL)")
    _line(df, x, "PLT", "혈소판 추이 (×10³/µL)", "PLT (×10³/µL)")
    _line(df, x, "ANC", "ANC 추이 (/µL)", "ANC (/µL)")
    if "CRP" in df.columns:
        _line(df, x, "CRP", "CRP 추이 (mg/dL)", "CRP (mg/dL)")
