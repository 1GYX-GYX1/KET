from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

TECH_LABELS = {
    "PT": "Pump and Treat (P&T)",
    "ISCO": "In-Situ Chemical Oxidation (ISCO)",
    "MNA": "Monitored Natural Attenuation (MNA)",
    "BIO": "Bioremediation",
    "PRB": "Permeable Reactive Barrier (PRB)",
    "AS": "Air Sparging (AS)",
}

STATE_LABELS = {
    "compliant": "Compliant / Green maintenance",
    "rebound": "Rebound detected",
    "tailing": "Tailing / Plateau detected",
    "progressing": "Ongoing improvement",
    "insufficient_history": "Initial stage",
}

RESEARCH_PRESET = {
    "Hydrogeological conditions": "Fractured aquifer / sandy media / moderate permeability",
    "Soil texture and physicochemical properties": "Medium permeability; groundwater-affected zone",
    "Secondary pollution prevention measures": "Real-time monitoring during remediation",
    "Risk control and remediation targets": "Groundwater contaminant concentration below target threshold",
    "Relevant industries": "Chemical manufacturing",
    "Industry subcategory codes": "261",
    "Organic contaminant": "Benzene",
    "Chemical formulas": "C6H6",
    "Contamination distribution range": "Groundwater pollution depth between 3 and 6 m",
    "Cost": "medium",
    "Duration": "medium",
    "Scope of work": "Groundwater remediation",
    "Construction requirements and impacts": "Maintain monitoring and control engineering disturbance",
}


@dataclass
class TrendConfig:
    rebound_relative_threshold: float = 0.50
    tailing_overall_improve_max: float = 0.30
    severe_threshold: float = 400.0
    mild_threshold: float = 50.0
    default_target_value: float = 40.0


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.lower() == "nan" else s


def parse_optional_float(text: Any) -> Optional[float]:
    s = normalize_text(text)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_time(ts: Any) -> Optional[datetime]:
    s = normalize_text(ts)
    if not s:
        return None
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def severity_from_concentration(value: float, severe_threshold: float, mild_threshold: float) -> str:
    if value >= severe_threshold:
        return "severe"
    if value <= mild_threshold:
        return "mild"
    return "moderate"


def analyze_trend(history: List[Dict[str, Any]], current_value: float, target_value: float, config: TrendConfig) -> Dict[str, Any]:
    if current_value <= target_value:
        return {
            "state_label": "compliant",
            "strategy_bias": "switch_to_green_or_monitoring",
            "reasons": ["The monitored concentration is below the target threshold. A low-disturbance polishing or maintenance strategy is suggested."],
        }

    if not history:
        return {
            "state_label": "insufficient_history",
            "strategy_bias": "collect_more_data",
            "reasons": ["This is the initial stage and historical monitoring data are limited. A conservative initial remediation pathway is suggested."],
        }

    prev_val = float(history[-1]["monitored_value"])
    change_rate = (prev_val - current_value) / prev_val if prev_val > 0 else 0.0

    if current_value > prev_val * (1 + config.rebound_relative_threshold):
        return {
            "state_label": "rebound",
            "strategy_bias": "strengthen_or_reintroduce_aggressive_control",
            "reasons": ["The concentration shows a clear rebound relative to the previous observation. A stronger reduction-oriented technology is suggested."],
        }

    if change_rate < config.tailing_overall_improve_max:
        return {
            "state_label": "tailing",
            "strategy_bias": "strengthen_or_reintroduce_aggressive_control",
            "reasons": ["The improvement is limited and a tailing or plateau pattern is detected. A technology adjustment is suggested."],
        }

    return {
        "state_label": "progressing",
        "strategy_bias": "maintain_current",
        "reasons": ["The concentration is still decreasing. Maintaining the current main technology pathway with continued monitoring is suggested."],
    }


def predict_demo(severity: str, state_label: str) -> List[Dict[str, Any]]:
    if state_label == "compliant":
        return [
            {"code": "MNA", "score": 0.46},
            {"code": "BIO", "score": 0.28},
            {"code": "PRB", "score": 0.18},
        ]
    if state_label in {"rebound", "tailing"}:
        return [
            {"code": "ISCO", "score": 0.41},
            {"code": "PT", "score": 0.31},
            {"code": "AS", "score": 0.17},
        ]
    if severity == "severe":
        return [
            {"code": "PT", "score": 0.43},
            {"code": "ISCO", "score": 0.34},
            {"code": "AS", "score": 0.16},
        ]
    if severity == "moderate":
        return [
            {"code": "ISCO", "score": 0.36},
            {"code": "PRB", "score": 0.24},
            {"code": "PT", "score": 0.20},
        ]
    return [
        {"code": "MNA", "score": 0.39},
        {"code": "BIO", "score": 0.26},
        {"code": "PRB", "score": 0.21},
    ]


def human_tech_name(code: str) -> str:
    return TECH_LABELS.get(code, code)


def metric_box(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f'''<div style="background:#ffffff;border:1px solid #d9e0e7;border-radius:12px;padding:0.9rem 1rem;min-height:96px;">
        <div style="font-size:0.83rem;color:#6c7b89;margin-bottom:0.3rem;">{label}</div>
        <div style="font-size:1.15rem;color:#1e3449;font-weight:700;line-height:1.35;">{value}</div>
        <div style="margin-top:0.3rem;font-size:0.82rem;color:#6c7b89;">{sub}</div></div>''',
        unsafe_allow_html=True,
    )


def make_trend_figure(df: pd.DataFrame, indicator_name: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.update_layout(template="plotly_white", height=420, title="No monitoring history yet")
        return fig

    x = [parse_time(x) or x for x in df["Time"]]
    y = df["Monitored value"]
    text = df["Current recommendation"].fillna("").astype(str).tolist()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers+text",
            text=text,
            textposition="top center",
            line=dict(color="#2a4a63", width=3),
            marker=dict(size=9, color="#2a4a63", line=dict(color="#ffffff", width=1)),
            hovertemplate="Time: %{x}<br>Monitored value: %{y}<br>Recommendation: %{text}<extra></extra>",
        )
    )

    if df["Target value"].notna().any():
        target = float(df["Target value"].dropna().iloc[-1])
        fig.add_hline(
            y=target,
            line=dict(color="#8a6b3f", width=2, dash="dash"),
            annotation_text=f"Target {target}",
            annotation_position="top left",
        )

    fig.update_layout(
        template="plotly_white",
        height=460,
        margin=dict(l=20, r=20, t=50, b=20),
        title=f"{indicator_name} concentration trend and recommendation evolution",
        xaxis_title="Monitoring time",
        yaxis_title="Monitored value",
    )
    return fig


def history_to_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for rec in records:
        rows.append(
            {
                "Time": rec.get("timestamp"),
                "Monitored value": rec.get("monitored_value"),
                "Target value": rec.get("target_value"),
                "Severity": rec.get("severity", ""),
                "Current recommendation": human_tech_name(rec.get("final_single_tech", "")),
                "State": STATE_LABELS.get(rec.get("state_label", ""), rec.get("state_label", "")),
                "Explanation": " ".join(rec.get("reasons", [])),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.assign(_sort=df["Time"].apply(parse_time)).sort_values("_sort", ascending=True).drop(columns=["_sort"])
    return df


def main() -> None:
    st.set_page_config(page_title="Intelligent Decision Support System for Dynamic Remediation Strategies of Contaminated Sites", layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background-color: #f7f8fa; }
        section[data-testid="stSidebar"] { background-color: #eef2f6; }
        .block-container { max-width: 1380px; padding-top: 1.2rem; padding-bottom: 2rem; }
        .title-box { background: #ffffff; border: 1px solid #d9e0e7; border-left: 6px solid #24415c; border-radius: 12px; padding: 1rem 1.1rem 0.85rem 1.1rem; margin-bottom: 0.9rem; }
        .title-box h1 { font-size: 1.65rem; margin: 0; color: #1e3449; font-weight: 700; }
        .card { background: #ffffff; border: 1px solid #d9e0e7; border-radius: 12px; padding: 0.95rem 1rem; margin-bottom: 0.8rem; }
        .section-head { color: #1e3449; font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.75rem 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="title-box"><h1>Intelligent Decision Support System for Dynamic Remediation Strategies of Contaminated Sites</h1></div>', unsafe_allow_html=True)

    if "history_records" not in st.session_state:
        st.session_state.history_records = []

    st.sidebar.header("Site feature inputs")
    hydro = st.sidebar.text_area("Hydrogeological conditions", value=RESEARCH_PRESET["Hydrogeological conditions"], height=100)
    soil = st.sidebar.text_area("Soil texture and physicochemical properties", value=RESEARCH_PRESET["Soil texture and physicochemical properties"], height=80)
    spm = st.sidebar.text_area("Secondary pollution prevention measures", value=RESEARCH_PRESET["Secondary pollution prevention measures"], height=80)
    target_text = st.sidebar.text_area("Risk control and remediation targets", value=RESEARCH_PRESET["Risk control and remediation targets"], height=80)
    org = st.sidebar.text_input("Organic contaminant", value=RESEARCH_PRESET["Organic contaminant"])
    formula = st.sidebar.text_input("Chemical formulas", value=RESEARCH_PRESET["Chemical formulas"])
    rel_ind = st.sidebar.text_input("Relevant industries", value=RESEARCH_PRESET["Relevant industries"])
    ind_code = st.sidebar.text_input("Industry subcategory codes", value=RESEARCH_PRESET["Industry subcategory codes"])
    severity_input = st.sidebar.text_input("Contamination severity (optional, auto-detected if blank)", value="")
    cont_range = st.sidebar.text_input("Contamination distribution range", value=RESEARCH_PRESET["Contamination distribution range"])
    cost = st.sidebar.text_input("Cost", value=RESEARCH_PRESET["Cost"])
    duration = st.sidebar.text_input("Duration", value=RESEARCH_PRESET["Duration"])
    scope = st.sidebar.text_input("Scope of work", value=RESEARCH_PRESET["Scope of work"])
    impact = st.sidebar.text_area("Construction requirements and impacts", value=RESEARCH_PRESET["Construction requirements and impacts"], height=80)

    config = TrendConfig()
    with st.sidebar.expander("Threshold parameters", expanded=False):
        config.severe_threshold = st.number_input("Severe threshold", min_value=0.0, value=400.0, step=10.0)
        config.mild_threshold = st.number_input("Mild threshold", min_value=0.0, value=50.0, step=1.0)
        config.default_target_value = st.number_input("Default target value", min_value=0.0, value=40.0, step=1.0)
        config.rebound_relative_threshold = st.number_input("Rebound threshold", min_value=0.0, value=0.50, step=0.05)
        config.tailing_overall_improve_max = st.number_input("Tailing threshold", min_value=0.0, max_value=0.99, value=0.30, step=0.05)

    st.markdown('<div class="card"><div class="section-head">Dynamic monitoring input</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.2, 1.0])
    with c1:
        timestamp = st.text_input("Current monitoring time", value="2026-04")
    with c2:
        monitored_value_text = st.text_input("Current monitored value (μg/L)", value="120")
    b1, b2 = st.columns([1.1, 1.1])
    run_btn = b1.button("Run decision", use_container_width=True)
    reset_btn = b2.button("Clear current browser session history", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if reset_btn:
        st.session_state.history_records = []
        st.success("The current browser session history has been cleared.")

    if run_btn:
        monitored_value = parse_optional_float(monitored_value_text)
        target_value = float(config.default_target_value)
        if monitored_value is None:
            st.error("The monitored value cannot be empty and must be numeric.")
        else:
            severity = normalize_text(severity_input).lower()
            if not severity:
                severity = severity_from_concentration(monitored_value, config.severe_threshold, config.mild_threshold)

            trend = analyze_trend(st.session_state.history_records, monitored_value, target_value, config)
            ranking = predict_demo(severity, trend["state_label"])
            final_single_tech = ranking[0]["code"]

            st.session_state.history_records.append(
                {
                    "timestamp": timestamp,
                    "monitored_value": monitored_value,
                    "target_value": target_value,
                    "severity": severity,
                    "state_label": trend["state_label"],
                    "reasons": trend["reasons"],
                    "final_single_tech": final_single_tech,
                    "ranking": ranking,
                    "snapshot": {
                        "Hydrogeological conditions": hydro,
                        "Soil texture and physicochemical properties": soil,
                        "Secondary pollution prevention measures": spm,
                        "Risk control and remediation targets": target_text,
                        "Organic contaminant": org,
                        "Chemical formulas": formula,
                        "Relevant industries": rel_ind,
                        "Industry subcategory codes": ind_code,
                        "Contamination distribution range": cont_range,
                        "Cost": cost,
                        "Duration": duration,
                        "Scope of work": scope,
                        "Construction requirements and impacts": impact,
                    },
                }
            )
            st.success("The demonstration decision has been generated.")

    records = st.session_state.history_records
    if records:
        latest = records[-1]

        st.markdown('<div class="card"><div class="section-head">Current status assessment</div>', unsafe_allow_html=True)
        cs1, cs2 = st.columns([1.0, 1.0])
        with cs1:
            metric_box("Engine state", STATE_LABELS.get(latest["state_label"], latest["state_label"]), "Rule-based demonstration engine")
        with cs2:
            metric_box("Current monitoring summary", f'{latest["monitored_value"]:.2f} μg/L', f'Target {latest["target_value"]:.2f} μg/L')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">Current recommendation</div>', unsafe_allow_html=True)
        st.write(f"**Recommended technology:** {human_tech_name(latest['final_single_tech'])}")
        st.write(f"**Interpretation:** {' '.join(latest['reasons'])}")
        rank_df = pd.DataFrame(
            [
                {"Rank": idx + 1, "Technology": human_tech_name(item["code"]), "Score": item["score"]}
                for idx, item in enumerate(latest["ranking"])
            ]
        )
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        hist_df = history_to_df(records)
        st.markdown('<div class="card"><div class="section-head">Historical monitoring sequence</div>', unsafe_allow_html=True)
        st.plotly_chart(make_trend_figure(hist_df, "Target contaminant"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">Decision log</div>', unsafe_allow_html=True)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
