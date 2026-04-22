
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="KET-based Remediation Decision Platform", layout="wide")

TECHNOLOGY_ORDER = ["AOPs", "AS", "P&T", "ISCO", "ISCR", "ISB", "SF", "SS", "MNA", "PRB"]
TECH_LABELS = {
    "AOPs": "Advanced Oxidation Processes (AOPs)",
    "AS": "Air Sparging (AS)",
    "P&T": "Pump and Treat (P&T)",
    "ISCO": "In-Situ Chemical Oxidation (ISCO)",
    "ISCR": "In-Situ Chemical Reduction (ISCR)",
    "ISB": "In-situ Bioremediation (ISB)",
    "SF": "Soil Flushing (SF)",
    "SS": "Solidification/Stabilization (SS)",
    "MNA": "Monitored Natural Attenuation (MNA)",
    "PRB": "Permeable Reactive Barrier (PRB)",
}

DEFAULT_SCORE_PROFILES = {
    "initial_severe": {"P&T": 0.36, "ISCO": 0.28, "AS": 0.14, "AOPs": 0.08, "PRB": 0.06, "MNA": 0.03, "ISB": 0.02, "ISCR": 0.01, "SF": 0.01, "SS": 0.01},
    "progressing_severe": {"P&T": 0.34, "ISCO": 0.30, "AS": 0.14, "AOPs": 0.07, "PRB": 0.06, "MNA": 0.03, "ISB": 0.02, "ISCR": 0.02, "SF": 0.01, "SS": 0.01},
    "rebound_severe": {"ISCO": 0.33, "P&T": 0.25, "AOPs": 0.14, "AS": 0.11, "PRB": 0.06, "ISCR": 0.04, "ISB": 0.03, "MNA": 0.02, "SF": 0.01, "SS": 0.01},
    "tailing_severe": {"ISCO": 0.35, "P&T": 0.22, "PRB": 0.12, "AS": 0.10, "AOPs": 0.08, "ISB": 0.05, "MNA": 0.03, "ISCR": 0.03, "SF": 0.01, "SS": 0.01},
    "initial_moderate": {"ISCO": 0.31, "P&T": 0.24, "PRB": 0.12, "AS": 0.10, "ISB": 0.08, "AOPs": 0.06, "MNA": 0.04, "ISCR": 0.03, "SF": 0.01, "SS": 0.01},
    "progressing_moderate": {"ISCO": 0.30, "P&T": 0.22, "PRB": 0.13, "ISB": 0.10, "AS": 0.09, "AOPs": 0.05, "MNA": 0.05, "ISCR": 0.04, "SF": 0.01, "SS": 0.01},
    "tailing_moderate": {"ISCO": 0.27, "PRB": 0.18, "ISB": 0.14, "P&T": 0.12, "AS": 0.09, "MNA": 0.08, "AOPs": 0.05, "ISCR": 0.04, "SF": 0.02, "SS": 0.01},
    "initial_mild": {"MNA": 0.24, "ISB": 0.20, "PRB": 0.16, "ISCO": 0.11, "P&T": 0.08, "ISCR": 0.07, "AS": 0.05, "AOPs": 0.04, "SF": 0.03, "SS": 0.02},
    "progressing_mild": {"MNA": 0.28, "ISB": 0.20, "PRB": 0.17, "ISCO": 0.10, "ISCR": 0.08, "P&T": 0.06, "AS": 0.04, "AOPs": 0.03, "SF": 0.02, "SS": 0.02},
    "tailing_mild": {"PRB": 0.24, "ISB": 0.20, "MNA": 0.17, "ISCO": 0.12, "ISCR": 0.10, "P&T": 0.06, "AS": 0.04, "AOPs": 0.03, "SF": 0.02, "SS": 0.02},
    "compliant_mild": {"MNA": 0.33, "ISB": 0.20, "PRB": 0.17, "ISCO": 0.09, "ISCR": 0.07, "P&T": 0.05, "AS": 0.03, "AOPs": 0.03, "SF": 0.02, "SS": 0.01},
    "case_t1": {"P&T": 0.43, "ISCO": 0.34, "AS": 0.16, "PRB": 0.03, "AOPs": 0.02, "MNA": 0.01, "ISB": 0.01, "ISCR": 0.00, "SF": 0.00, "SS": 0.00},
    "case_t2": {"ISCO": 0.39, "AS": 0.27, "PRB": 0.18, "P&T": 0.07, "AOPs": 0.04, "ISCR": 0.03, "ISB": 0.01, "MNA": 0.01, "SF": 0.00, "SS": 0.00},
    "case_t3": {"MNA": 0.41, "ISB": 0.24, "PRB": 0.19, "ISCO": 0.07, "ISCR": 0.04, "P&T": 0.03, "AS": 0.01, "AOPs": 0.01, "SF": 0.00, "SS": 0.00},
}
DEFAULT_DECISION_PARAMS = {
    "target_value": 40.0,
    "severe_threshold": 400.0,
    "mild_threshold": 50.0,
    "rebound_ratio": 0.15,
    "tailing_improvement_ratio": 0.20,
}

def get_secret_dict(key: str, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        raw = st.secrets.get(key, {})
        return dict(raw) if raw else default
    except Exception:
        return default

SCORE_PROFILES = get_secret_dict("score_profiles", DEFAULT_SCORE_PROFILES)
DECISION_PARAMS = get_secret_dict("decision_params", DEFAULT_DECISION_PARAMS)

def normalize_profile(profile_name: str) -> Dict[str, float]:
    raw = SCORE_PROFILES.get(profile_name, {})
    profile = {tech: float(raw.get(tech, 0.0)) for tech in TECHNOLOGY_ORDER}
    s = sum(profile.values())
    if s > 0:
        profile = {k: v / s for k, v in profile.items()}
    return profile

def parse_time(value: str) -> Optional[datetime]:
    txt = str(value).strip()
    if not txt:
        return None
    for fmt in ("%Y-%m", "%Y/%m", "%Y-%m-%d", "%Y/%m/%d", "%B %Y", "%b %Y"):
        try:
            return datetime.strptime(txt, fmt)
        except ValueError:
            continue
    return None

def severity_from_value(value: float, severe_thr: float, mild_thr: float) -> str:
    if value >= severe_thr:
        return "severe"
    if value <= mild_thr:
        return "mild"
    return "moderate"

def determine_general_state(history: List[Dict[str, Any]], current_value: float, target: float, severe_thr: float, mild_thr: float, rebound_ratio: float, tailing_ratio: float):
    severity = severity_from_value(current_value, severe_thr, mild_thr)
    if current_value <= target:
        return "compliant_mild", "compliant", "post-compliance monitoring"
    if not history:
        return f"initial_{severity}", f"initial_{severity}", "initial startup"
    prev = history[-1]["concentration"]
    if prev > 0 and current_value >= prev * (1 + rebound_ratio):
        return f"rebound_{severity}" if f"rebound_{severity}" in SCORE_PROFILES else f"progressing_{severity}", f"rebound_{severity}", "rebound suspected"
    improvement = (prev - current_value) / prev if prev > 0 else 0.0
    if len(history) >= 2:
        prev2 = history[-2]["concentration"]
        long_improvement = (prev2 - current_value) / prev2 if prev2 > 0 else 0.0
    else:
        long_improvement = improvement
    if improvement < tailing_ratio and long_improvement < max(tailing_ratio * 1.2, 0.25):
        profile = f"tailing_{severity}" if f"tailing_{severity}" in SCORE_PROFILES else f"progressing_{severity}"
        return profile, f"tailing_{severity}", "tailing confirmed"
    return f"progressing_{severity}", f"progressing_{severity}", "control pathway continues"

def determine_case_state(history: List[Dict[str, Any]], current_value: float, target: float):
    n = len(history)
    if current_value <= target:
        return "case_t3", "T3", "post-compliance monitoring"
    if n <= 2:
        return "case_t1", "T1", "early-stage intensive control"
    return "case_t2", "T2", "mid-stage strategy adjustment"

def profile_to_table(profile_name: str) -> pd.DataFrame:
    profile = normalize_profile(profile_name)
    rows = [{"Technology": TECH_LABELS[t], "Code": t, "Score": round(profile[t], 4)} for t in TECHNOLOGY_ORDER]
    return pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)

def best_tech(profile_name: str) -> str:
    profile = normalize_profile(profile_name)
    return max(profile.items(), key=lambda kv: kv[1])[0]

def make_chart(df: pd.DataFrame, target_value: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["concentration"],
        mode="lines+markers+text",
        text=df["technology_code"],
        textposition="top center",
        line=dict(width=3, color="#355875"),
        marker=dict(size=8, color="#355875"),
        name="Recommendation pathway",
    ))
    fig.add_hline(y=target_value, line=dict(color="#9b6b2f", width=2, dash="dash"),
                  annotation_text=f"Target {target_value}", annotation_position="bottom left")
    fig.update_layout(
        template="plotly_white",
        height=470,
        margin=dict(l=20, r=20, t=60, b=20),
        title="KET-guided target-contaminant concentration trend and remediation recommendation evolution",
        xaxis_title="Monitoring time",
        yaxis_title="Monitored value",
        showlegend=False,
    )
    return fig

def init_state():
    if "records" not in st.session_state:
        st.session_state.records = []

init_state()

st.markdown("""
<style>
.stApp { background-color: #f7f8fa; }
section[data-testid="stSidebar"] { background-color: #eef2f6; }
.block-container { max-width: 1380px; padding-top: 1.2rem; padding-bottom: 2rem; }
.title-box { background: #ffffff; border: 1px solid #d9e0e7; border-left: 6px solid #24415c; border-radius: 12px; padding: 1rem 1.1rem 0.85rem 1.1rem; margin-bottom: 0.9rem; }
.card { background: #ffffff; border: 1px solid #d9e0e7; border-radius: 12px; padding: 0.95rem 1rem; margin-bottom: 0.8rem; }
.section-head { color: #1e3449; font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.75rem 0; }
.metric-box { background: #ffffff; border: 1px solid #d9e0e7; border-radius: 12px; padding: 0.9rem 1rem; min-height: 96px; }
.metric-label { font-size: 0.83rem; color: #6c7b89; margin-bottom: 0.3rem; }
.metric-value { font-size: 1.15rem; color: #1e3449; font-weight: 700; line-height: 1.35; }
.metric-sub { margin-top: 0.3rem; font-size: 0.82rem; color: #6c7b89; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-box"><h1>KET-Based Intelligent Decision Support System for Dynamic Remediation Strategies of Contaminated Sites</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("KET input features")
    mode = st.radio("Decision mode", ["General dynamic decision", "Manuscript case reproduction"], index=0)
    st.caption("Use general mode for arbitrary scenarios. Use manuscript mode only to reproduce the case-study pathway in the paper.")

    with st.expander("Hydrogeological perspective", expanded=True):
        hydro = st.text_area("Hydrogeological conditions", value="")
        soil = st.text_area("Soil texture and physicochemical properties", value="")
    with st.expander("Remediation objective perspective", expanded=True):
        spm = st.text_area("Secondary pollution prevention measures", value="")
        target_text = st.text_area("Risk control and remediation targets", value="")
        rel_ind = st.text_input("Relevant industries", value="")
        ind_code = st.text_input("Industry subcategory codes", value="")
    with st.expander("Contaminant properties perspective", expanded=True):
        heavy = st.text_input("Heavy metals", value="")
        chem_symbols = st.text_input("Chemical symbols", value="")
        org = st.text_input("Organic contaminants", value="")
        formulas = st.text_input("Chemical formulas", value="")
        abbr = st.text_input("Abbreviations", value="")
        other = st.text_input("Other pollutants", value="")
    with st.expander("Site pollution characteristics perspective", expanded=True):
        severity_text = st.text_input("Contamination severity (optional)", value="")
        dist_range = st.text_input("Contamination distribution range", value="")
    with st.expander("Engineering-economic perspective", expanded=True):
        cost = st.text_input("Cost", value="")
        duration = st.text_input("Duration", value="")
        scope = st.text_input("Scope of work", value="")
        impacts = st.text_area("Construction requirements and impacts", value="")

    with st.expander("Decision parameters", expanded=False):
        target_value = st.number_input("Target value", min_value=0.0, value=float(DECISION_PARAMS.get("target_value", 40.0)))
        severe_thr = st.number_input("Severe threshold", min_value=0.0, value=float(DECISION_PARAMS.get("severe_threshold", 400.0)))
        mild_thr = st.number_input("Mild threshold", min_value=0.0, value=float(DECISION_PARAMS.get("mild_threshold", 50.0)))
        rebound_ratio = st.number_input("Rebound ratio", min_value=0.0, value=float(DECISION_PARAMS.get("rebound_ratio", 0.15)), step=0.05)
        tailing_ratio = st.number_input("Tailing improvement ratio", min_value=0.0, value=float(DECISION_PARAMS.get("tailing_improvement_ratio", 0.20)), step=0.05)

st.markdown('<div class="card"><div class="section-head">Dynamic monitoring input</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    current_time = st.text_input("Current monitoring time", value="")
with c2:
    current_value = st.text_input("Current monitored value (μg/L)", value="")
b1, b2 = st.columns(2)
run = b1.button("Run decision", use_container_width=True)
clear = b2.button("Clear current browser session history", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if clear:
    st.session_state.records = []
    st.success("Browser-session history has been cleared.")

if run:
    try:
        val = float(current_value)
        history = st.session_state.records
        if mode == "Manuscript case reproduction":
            profile_name, phase, diagnosis = determine_case_state(history, val, target_value)
        else:
            profile_name, phase, diagnosis = determine_general_state(
                history, val, target_value, severe_thr, mild_thr, rebound_ratio, tailing_ratio
            )
        sev = severity_from_value(val, severe_thr, mild_thr)
        if severity_text.strip():
            sev = severity_text.strip().lower()
        tech_code = best_tech(profile_name)
        st.session_state.records.append({
            "date": current_time.strip() or f"Record {len(history)+1}",
            "concentration": val,
            "phase": phase,
            "severity_feature": f"{sev.capitalize()} contamination scenario",
            "technology_code": tech_code,
            "technology": TECH_LABELS[tech_code],
            "diagnosis": diagnosis,
            "profile_name": profile_name,
        })
        st.success("Decision updated.")
    except Exception as exc:
        st.error(f"Decision execution failed: {exc}")

records = st.session_state.records
if records:
    latest = records[-1]
    st.markdown('<div class="card"><div class="section-head">Current recommendation</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.markdown(f'<div class="metric-box"><div class="metric-label">Recommended technology</div><div class="metric-value">{latest["technology"]}</div><div class="metric-sub">{latest["phase"]}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-box"><div class="metric-label">Diagnosis</div><div class="metric-value">{latest["diagnosis"]}</div><div class="metric-sub">{latest["severity_feature"]}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-box"><div class="metric-label">Score profile</div><div class="metric-value">{latest["profile_name"]}</div><div class="metric-sub">Read from private deployment secrets</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="section-head">KET-informed technology scores</div>', unsafe_allow_html=True)
    st.dataframe(profile_to_table(latest["profile_name"]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    df = pd.DataFrame(records)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(make_chart(df, target_value), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    show_df = df[["date", "concentration", "phase", "severity_feature", "technology", "diagnosis"]]
    st.markdown('<div class="card"><div class="section-head">Historical KET-aligned decision log</div>', unsafe_allow_html=True)
    st.dataframe(show_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No decision record yet. Please enter a monitoring value and run the decision module.")
