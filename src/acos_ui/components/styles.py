from __future__ import annotations
from typing import Any


CSS = """
<style>
.block-container {padding-top: 1.25rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,.22);
    border-radius: 14px;
    padding: 14px 16px;
    background: rgba(128,128,128,.035);
}
.acos-hero {
    border: 1px solid rgba(128,128,128,.22);
    border-radius: 18px;
    padding: 22px 24px;
    margin: 4px 0 18px 0;
    background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(14,165,233,.06));
}
.acos-hero h2 {margin: 0 0 6px 0;}
.acos-muted {opacity: .74;}
.acos-agent-card {
    border: 1px solid rgba(128,128,128,.22);
    border-radius: 16px;
    padding: 16px;
    min-height: 320px;
    background: rgba(128,128,128,.025);
}
.acos-agent-title {font-size: 1.08rem; font-weight: 700;}
.acos-operation {font-size: 1.42rem; font-weight: 750; margin: 8px 0;}
.acos-pill {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(99,102,241,.14);
    margin: 2px 4px 2px 0;
    font-size: .82rem;
}
.acos-plan {
    border-left: 5px solid #6366f1;
    border-radius: 14px;
    padding: 18px 20px;
    background: rgba(99,102,241,.08);
    margin: 8px 0 18px 0;
}
.acos-flow-node {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    background: rgba(128,128,128,.035);
}
.acos-arrow {font-size: 1.45rem; text-align: center; opacity: .7; padding-top: 20px;}
.acos-section-title {font-size: 1.25rem; font-weight: 750; margin: 12px 0 8px;}

.acos-landing-hero {
    border-radius: 22px;
    padding: 34px 36px;
    margin-bottom: 22px;
    color: white;
    background:
      radial-gradient(circle at top right, rgba(56,189,248,.38), transparent 38%),
      linear-gradient(135deg, #172554, #312e81 58%, #0f766e);
}
.acos-landing-hero h1 {
    margin: 8px 0;
    font-size: 2.35rem;
}
.acos-landing-hero p {
    max-width: 720px;
    font-size: 1.08rem;
    opacity: .9;
}
.acos-eyebrow {
    font-size: .78rem;
    letter-spacing: .14em;
    opacity: .8;
}
.acos-architecture-number {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-weight: 750;
    color: white;
    background: #4f46e5;
    margin-top: 8px;
}
.acos-architecture-arrow {
    margin-left: 21px;
    font-size: 1.55rem;
    opacity: .5;
    line-height: 1;
}
.acos-profile-hero {
    display: flex;
    align-items: center;
    gap: 18px;
    border: 1px solid rgba(128,128,128,.22);
    border-radius: 18px;
    padding: 22px;
    margin: 12px 0 20px 0;
    background: rgba(99,102,241,.06);
}
.acos-profile-hero h2 {margin: 0;}
.acos-profile-icon {
    width: 68px;
    height: 68px;
    border-radius: 18px;
    display: grid;
    place-items: center;
    font-size: 2rem;
    background: rgba(99,102,241,.13);
}
</style>
"""


def apply_styles(st: Any) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
