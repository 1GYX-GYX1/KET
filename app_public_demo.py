from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# Public demo constants
# NOTE:
# - Technology names are public metadata only.
# - Recommendation scores are NOT stored in this public file.
# - Scores are loaded from Streamlit secrets during deployment.
# ---------------------------------------------------------------------
TECH_METADATA = [
    ("AOPs", "Advanced Oxidation Processes"),
    ("AS", "Air Sparging"),
    ("P&T", "Pump and Treat"),
    ("ISCO", "In-Situ Chemical Oxidation"),
    ("ISCR", "In-Situ Chemical Reduction"),
    ("ISB", "In-Situ Bioremediation"),
    ("SF", "Soil Flushing"),
    ("SS", "Solidification/Stabilization"),
    ("MNA", "Monitored Natural Attenuation"),
    ("PRB", "Permeable Reactive Barrier"),
]
TECH_CODE_ORDER = [code for code, _ in TECH_METADATA]
TECH_LABELS = {code: f"{name} ({code})" for code, name in TECH_METADATA}

STATE_LABELS = {
    "compliant": "Post-compliance maintenance stage",
    "rebound": "Rebound suspected",
    "tailing": "Tailing or plateau confirmed",
    "progressing": "Ongoing improvement",
    "insufficient_history": "Initial stage",
}

PERSPECTIVE_GROUPS = {
    "Hydrogeological perspective": [
        "Hydrogeological conditions",
        "Soil texture and physicochemical properties",
    ],
    "Remediation objective perspective": [
        "Secondary pollution prevention measures",
        "Risk control and remediation targets",
        "Relevant industries",
        "Industry subcategory codes",
    ],
    "Contaminant properties perspective": [
        "Heavy metals",
        "Chemical symbols",
        "Organic contaminant",
        "Chemical formulas",
        "Abbreviations",
        "Other contaminants",
    ],
    "Site pollution characteristics perspective": [
        "Contamination severity (optional; leave blank for automatic inference)",
        "Contamination distribution range",
    ],
    "Engineering-economic perspective": [
        "Cost",
        "Duration",
        "Scope of work",
        "Construction requirements and impacts",
    ],
}


@dataclass
class TrendConfig:
    rebound_relative_threshold: float = 0.50
    tailing_overall_improve_max: float = 0.30
    severe_threshold: float = 400.0
    mild_threshold: float = 50.0
    default_target_value: float = 40.0


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
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
    for fmt in ["%y年%m月", "%Y年%m月"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None



def human_tech_name(code: str) -> str:
    return TECH_LABELS.get(code, code)



def severity_from_concentration(value: float, severe_threshold: float, mild_threshold: float) -> str:
    if value >= severe_threshold:
        return "severe"
    if value <= mild_threshold:
        return "mild"
    return "moderate"



def severity_phrase(severity: str) -> str:
    return {
        "severe": "Severe contamination scenario",
        "moderate": "Moderate contamination scenario",
        "mild": "Mild contamination scenario",
    }.get(severity, "Contaminated-site scenario")



def build_ket_explanation(profile_key: str, state_label: str, severity: str) -> str:
    explanation_map = {
        "initial_severe": "The current scenario is interpreted under the KET-aligned severe-stage setting. The score panel reflects a confidential deployment profile corresponding to an initial high-risk groundwater remediation stage.",
        "progressing_severe": "The current scenario is interpreted under the KET-aligned progressing severe-stage setting. The score panel reflects a confidential deployment profile corresponding to continued high-intensity control under ongoing improvement.",
        "rebound_severe": "The current scenario is interpreted under the KET-aligned rebound severe-stage setting. The score panel reflects a confidential deployment profile corresponding to rebound-sensitive control strengthening.",
        "tailing_severe": "The current scenario is interpreted under the KET-aligned tailing severe-stage setting. The score panel reflects a confidential deployment profile corresponding to source-reduction adjustment after tailing recognition.",
        "progressing_moderate": "The current scenario is interpreted under the KET-aligned moderate-stage setting. The score panel reflects a confidential deployment profile corresponding to balanced remediation control under a moderate contamination stage.",
        "tailing_moderate": "The current scenario is interpreted under the KET-aligned tailing moderate-stage setting. The score panel reflects a confidential deployment profile corresponding to intensified source treatment after limited marginal improvement.",
        "compliant_mild": "The current scenario is interpreted under the KET-aligned post-compliance mild-stage setting. The score panel reflects a confidential deployment profile corresponding to low-disturbance maintenance and long-term risk control.",
    }
    default_text = "The displayed technology scores are loaded from a private deployment configuration aligned with the KET framework, while confidential training assets and proprietary model parameters remain undisclosed."
    return explanation_map.get(profile_key, default_text) + f" Current state: {STATE_LABELS.get(state_label, state_label)}. Interpreted severity: {severity_phrase(severity)}."


# ---------------------------------------------------------------------
# Trend analysis (public deterministic shell)
# ---------------------------------------------------------------------
def analyze_trend(history: List[Dict[str, Any]], current_value: float, target_value: float, config: TrendConfig) -> Dict[str, Any]:
    if current_value <= target_value:
        return {
            "state_label": "compliant",
            "diagnosis": "post_compliance_monitoring",
            "reasons": [
                "The monitored concentration is below the target threshold. Low-disturbance post-compliance management is appropriate."
            ],
        }

    if not history:
        return {
            "state_label": "insufficient_history",
            "diagnosis": "initial_startup",
            "reasons": [
                "Historical monitoring records are not yet available. The decision is generated under an initial-stage scenario."
            ],
        }

    prev_val = float(history[-1]["concentration"])
    change_rate = (prev_val - current_value) / prev_val if prev_val > 0 else 0.0

    if current_value > prev_val * (1 + config.rebound_relative_threshold):
        return {
            "state_label": "rebound",
            "diagnosis": "rebound_suspected",
            "reasons": [
                "A rebound relative to the previous observation is detected. Strengthened control should be considered."
            ],
        }

    if change_rate < config.tailing_overall_improve_max:
        return {
            "state_label": "tailing",
            "diagnosis": "tailing_confirmed",
            "reasons": [
                "The concentration decrease is limited, indicating a tailing or plateau pattern. A source-reduction adjustment should be considered."
            ],
        }

    return {
        "state_label": "progressing",
        "diagnosis": "control_pathway_continues",
        "reasons": [
            "The concentration continues to decline. The current control pathway can be maintained under continued monitoring."
        ],
    }


# ---------------------------------------------------------------------
# Private score profile loader
# ---------------------------------------------------------------------
def get_private_score_profiles() -> Dict[str, Dict[str, float]]:
    """
    Scores are loaded from Streamlit secrets so the public repository does not
    expose confidential technology-score settings.
    """
    if "score_profiles" not in st.secrets:
        return {}

    profiles_raw = st.secrets["score_profiles"]
    profiles: Dict[str, Dict[str, float]] = {}
    for profile_name, profile_values in profiles_raw.items():
        profiles[profile_name] = {str(k): float(v) for k, v in dict(profile_values).items()}
    return profiles



def choose_profile_key(history: List[Dict[str, Any]], severity: str, trend: Dict[str, Any]) -> str:
    state = trend["state_label"]
    if state == "compliant":
        return "compliant_mild"
    if not history:
        return f"initial_{severity}"
    if state == "rebound":
        return f"rebound_{severity}"
    if state == "tailing":
        return f"tailing_{severity}"
    return f"progressing_{severity}"



def resolve_score_profile(profile_key: str, profiles: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    if profile_key in profiles:
        return profiles[profile_key]
    if profile_key.endswith("_mild") and "compliant_mild" in profiles:
        return profiles["compliant_mild"]
    return {}



def build_score_table(score_profile: Dict[str, float]) -> pd.DataFrame:
    rows = []
    for code in TECH_CODE_ORDER:
        score = float(score_profile.get(code, 0.0))
        rows.append(
            {
                "Technology": human_tech_name(code),
                "Code": code,
                "KET-informed recommendation score": score,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("KET-informed recommendation score", ascending=False).reset_index(drop=True)
    return df



def top_recommendation(score_df: pd.DataFrame) -> Tuple[str, str, float]:
    if score_df.empty:
        return "", "", 0.0
    row = score_df.iloc[0]
    return str(row["Code"]), str(row["Technology"]), float(row["KET-informed recommendation score"])


# ---------------------------------------------------------------------
# Figures and display helpers
# ---------------------------------------------------------------------
def make_trend_figure(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.update_layout(template="plotly_white", height=420, title="No monitoring history yet")
        return fig

    x = [parse_time(x) or x for x in df["date"]]
    y = df["concentration"]
    text = df["technology_code"].fillna("").astype(str).tolist()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers+text",
            text=text,
            textposition="top center",
            line=dict(color="#385a75", width=3),
            marker=dict(size=8, color="#385a75", line=dict(color="#ffffff", width=1)),
            hovertemplate="Time: %{x}<br>Monitored value: %{y}<br>Technology: %{text}<extra></extra>",
            showlegend=False,
        )
    )

    if df["target_value"].notna().any():
        target = float(df["target_value"].dropna().iloc[-1])
        fig.add_hline(
            y=target,
            line=dict(color="#9c6b32", width=2, dash="dash"),
            annotation_text=f"Target {target}",
            annotation_position="bottom left",
        )

    fig.update_layout(
        template="plotly_white",
        height=460,
        margin=dict(l=20, r=20, t=50, b=20),
        title="KET-guided target-contaminant concentration trend and remediation recommendation evolution",
        xaxis_title="Monitoring time",
        yaxis_title="Monitored value",
    )
    return fig



def metric_box(label: str, value: str, sub: str = "") -> None:
    st.markdown(
        f'''<div style="background:#ffffff;border:1px solid #d9e0e7;border-radius:12px;padding:0.9rem 1rem;min-height:96px;">
        <div style="font-size:0.83rem;color:#6c7b89;margin-bottom:0.3rem;">{label}</div>
        <div style="font-size:1.15rem;color:#1e3449;font-weight:700;line-height:1.35;">{value}</div>
        <div style="margin-top:0.3rem;font-size:0.82rem;color:#6c7b89;">{sub}</div></div>''',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Session history
# ---------------------------------------------------------------------
def init_history() -> List[Dict[str, Any]]:
    if "demo_history" not in st.session_state:
        st.session_state["demo_history"] = []
    return st.session_state["demo_history"]



def append_history(record: Dict[str, Any]) -> None:
    st.session_state["demo_history"].append(record)



def clear_history() -> None:
    st.session_state["demo_history"] = []



def history_to_df(records: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.assign(_sort=df["date"].apply(parse_time)).sort_values("_sort", ascending=True).drop(columns=["_sort"])
    return df


# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="KET-Based Decision Support System", layout="wide")

    st.markdown(
        """
        <style>
        .stApp { background-color: #f7f8fa; }
        section[data-testid="stSidebar"] { background-color: #eef2f6; }
        .block-container { max-width: 1380px; padding-top: 1.2rem; padding-bottom: 2rem; }
        .title-box { background: #ffffff; border: 1px solid #d9e0e7; border-left: 6px solid #24415c; border-radius: 12px; padding: 1rem 1.1rem 0.85rem 1.1rem; margin-bottom: 0.9rem; }
        .title-box h1 { font-size: 1.75rem; margin: 0; color: #1e3449; font-weight: 700; }
        .card { background: #ffffff; border: 1px solid #d9e0e7; border-radius: 12px; padding: 0.95rem 1rem; margin-bottom: 0.8rem; }
        .section-head { color: #1e3449; font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.75rem 0; }
        .info-box { background: #f8fbff; border: 1px solid #d9e7f2; border-radius: 10px; padding: 0.8rem 0.9rem; line-height: 1.7; color: #34506b; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="title-box"><h1>KET-Based Intelligent Decision Support System for Dynamic Remediation Strategies of Contaminated Sites</h1></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="card"><div class="section-head">Framework note</div><div class="info-box">This public interface is aligned with the five-perspective input structure and stage-wise output presentation of the KET framework. Confidential training data, proprietary weights, and deployment-specific score profiles are not exposed in the public repository.</div></div>',
        unsafe_allow_html=True,
    )

    config = TrendConfig()
    profiles = get_private_score_profiles()
    history = init_history()

    with st.sidebar:
        st.header("KET-aligned site feature input")
        values: Dict[str, str] = {}
        for group_name, fields in PERSPECTIVE_GROUPS.items():
            st.markdown(f"**{group_name}**")
            for label in fields:
                if label in {
                    "Hydrogeological conditions",
                    "Soil texture and physicochemical properties",
                    "Secondary pollution prevention measures",
                    "Risk control and remediation targets",
                    "Construction requirements and impacts",
                }:
                    values[label] = st.text_area(label, value="", height=90)
                else:
                    values[label] = st.text_input(label, value="")

        with st.expander("Adjustable interpretation parameters", expanded=False):
            config.severe_threshold = st.number_input("Severe threshold", min_value=0.0, value=400.0, step=10.0)
            config.mild_threshold = st.number_input("Mild threshold", min_value=0.0, value=50.0, step=1.0)
            config.default_target_value = st.number_input("Default target value", min_value=0.0, value=40.0, step=1.0)
            config.rebound_relative_threshold = st.number_input("Relative rebound threshold", min_value=0.0, value=0.50, step=0.05)
            config.tailing_overall_improve_max = st.number_input("Maximum overall improvement for tailing recognition", min_value=0.0, max_value=0.99, value=0.30, step=0.05)

    st.markdown('<div class="card"><div class="section-head">Dynamic monitoring input</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        timestamp = st.text_input("Current monitoring time", value="")
    with c2:
        monitored_value_text = st.text_input("Current monitored value (μg/L)", value="")

    b1, b2 = st.columns(2)
    run_btn = b1.button("Run KET-aligned decision", use_container_width=True)
    clear_btn = b2.button("Clear current browser session history", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if clear_btn:
        clear_history()
        st.success("Browser-session history has been cleared.")

    if run_btn:
        monitored_value = parse_optional_float(monitored_value_text)
        if monitored_value is None:
            st.error("Please enter a valid monitored value.")
        elif not profiles:
            st.error("Private KET score profiles have not been configured in Streamlit secrets yet.")
        else:
            severity_text = normalize_text(values["Contamination severity (optional; leave blank for automatic inference)"]).lower()
            if severity_text in {"severe", "moderate", "mild"}:
                severity = severity_text
            else:
                severity = severity_from_concentration(
                    monitored_value,
                    config.severe_threshold,
                    config.mild_threshold,
                )

            trend = analyze_trend(history, monitored_value, config.default_target_value, config)
            profile_key = choose_profile_key(history, severity, trend)
            score_profile = resolve_score_profile(profile_key, profiles)

            if not score_profile:
                st.error(f"No private KET score profile was found for scenario: {profile_key}")
            else:
                score_df = build_score_table(score_profile)
                tech_code, tech_name, tech_score = top_recommendation(score_df)
                record = {
                    "date": timestamp,
                    "concentration": monitored_value,
                    "target_value": config.default_target_value,
                    "phase": profile_key,
                    "severity_feature": severity_phrase(severity),
                    "technology": tech_name,
                    "technology_code": tech_code,
                    "diagnosis": trend["diagnosis"],
                    "engineering_note": " ".join(trend["reasons"]),
                    "ket_note": build_ket_explanation(profile_key, trend["state_label"], severity),
                    "recommendation_score": tech_score,
                }
                append_history(record)
                history = init_history()
                st.success("Decision completed and added to the current browser session history.")

    history_df = history_to_df(history)

    if history_df.empty:
        st.info("No recommendation has been generated in this browser session yet.")
    else:
        latest = history_df.iloc[-1]
        st.markdown('<div class="card"><div class="section-head">Current KET-aligned decision summary</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            metric_box("Current state", latest["diagnosis"], latest["severity_feature"])
        with m2:
            metric_box("Recommended technology", latest["technology"], latest["technology_code"])
        with m3:
            metric_box("Top KET-informed score", f"{float(latest['recommendation_score']):.1f}", latest["phase"])
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">KET-informed technology scores</div>', unsafe_allow_html=True)
        latest_phase = str(latest["phase"])
        latest_score_df = build_score_table(resolve_score_profile(latest_phase, profiles))
        st.dataframe(latest_score_df[["Technology", "KET-informed recommendation score"]], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">Engineering interpretation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">{latest["engineering_note"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">KET framework interpretation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">{latest["ket_note"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">KET-guided target-contaminant concentration trend and recommendation evolution</div>', unsafe_allow_html=True)
        st.plotly_chart(make_trend_figure(history_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="section-head">Historical KET-aligned decision log</div>', unsafe_allow_html=True)
        st.dataframe(
            history_df[["date", "concentration", "phase", "severity_feature", "technology", "diagnosis"]],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
