import os
import snowflake.connector
import pandas as pd
import streamlit as st
import pickle
import numpy as np
import altair as alt
from dotenv import load_dotenv

# Initialize application configuration mapping
load_dotenv()

# Set premium dashboard layout configuration
st.set_page_config(
    page_title="Elite IPL Strategy Engine",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Design tokens: "Dark Operations Center" — fully adapted for a premium
# dark slate canvas. Replaces warm light colors with deep muted panel tones
# (#222A3B) and sharp high-contrast text for maximum legibility in low light.
# ---------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-canvas: #F3F7F2; /* Soft sage app canvas */
        --bg-panel: rgba(251, 253, 248, 0.88);  /* Frosted warm panel */
        --bg-panel-2: rgba(244, 248, 239, 0.94); /* Elevated soft surface */
        --bg-panel-3: #FBFDF8; /* Input surface */
        --border-hair: rgba(15, 23, 42, 0.10); /* Soft light border */
        --border-hair-soft: rgba(15, 23, 42, 0.06);
        --text-primary: #0F172A; /* Slate ink */
        --text-secondary: #334155; /* Slate metadata */
        --text-muted: #64748B;
        --floodlight: #6D5DFB;
        --floodlight-dim: rgba(109, 93, 251, 0.12);
        --boundary: #0891B2;
        --boundary-dim: rgba(8, 145, 178, 0.12);
        --wicket: #F43F5E;
        --wicket-dim: rgba(244, 63, 94, 0.12);
        --shadow-card: 0 16px 42px rgba(15, 23, 42, 0.08);
        --shadow-card-hover: 0 22px 60px rgba(15, 23, 42, 0.14);
        --amber: #D97706;
        --amber-dim: rgba(217, 119, 6, 0.12);
    }

    html, body, .stApp {
        background: var(--bg-canvas) !important;
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        --primary-color: #0F766E !important;
        --primary-color-hover: #0E7490 !important;
        --primary-color-active: #115E59 !important;
        --secondary-background-color: #FBFDF8 !important;
        --text-color: #0F172A !important;
    }

    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #22D3EE 0%, #7C3AED 48%, #FB7185 100%);
        z-index: 999;
    }

    .stApp {
        background:
            radial-gradient(circle at 14% 8%, rgba(109,93,251,0.16), transparent 30%),
            radial-gradient(circle at 84% 10%, rgba(8,145,178,0.13), transparent 28%),
            radial-gradient(circle at 74% 82%, rgba(244,63,94,0.08), transparent 32%),
            linear-gradient(135deg, #FBFDF8 0%, var(--bg-canvas) 50%, #EAF4EC 100%) !important;
    }

    /* Numeric / scoreboard figures */
    .stat-mono { font-family: 'JetBrains Mono', monospace; }

    /* ---------- Sidebar ---------- */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(251,253,248,0.96), rgba(237,247,232,0.96));
        border-right: 1px solid var(--border-hair);
    }

    /* Add breathing room around the whole app */
    .block-container { padding-top: 1.6rem; }

    /* ---------- Hero header ---------- */
    .hero-wrap {
        position: relative;
        background:
            linear-gradient(135deg, rgba(251,253,248,0.95), rgba(235,247,239,0.90)),
            radial-gradient(circle at 18% 18%, rgba(8,145,178,0.14), transparent 32%),
            radial-gradient(circle at 82% 20%, rgba(109,93,251,0.20), transparent 38%);
        border: 1px solid var(--border-hair);
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 26px;
        box-shadow: var(--shadow-card);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
        overflow: hidden;
    }
    .hero-wrap::before {
        content: "";
        position: absolute;
        top: 0; right: 0;
        width: 340px; height: 100%;
        background: radial-gradient(ellipse at top right, rgba(34, 211, 238, 0.16) 0%, rgba(34, 211, 238, 0) 70%);
        pointer-events: none;
    }
    .hero-wrap::after {
        content: "";
        position: absolute;
        inset: auto -40px -72px auto;
        width: 260px;
        height: 180px;
        border-radius: 50%;
        border: 1px solid rgba(109,93,251,0.14);
        box-shadow: inset 0 0 45px rgba(109,93,251,0.16);
        transform: rotate(-12deg);
        pointer-events: none;
    }
    .hero-left { display: flex; align-items: center; gap: 16px; position: relative; z-index: 1; }
    .hero-badge {
        width: 52px; height: 52px;
        border-radius: 14px;
        background: linear-gradient(145deg, #22D3EE 0%, #7C3AED 100%);
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
        color: #FFFFFF;
        box-shadow: 0 12px 30px rgba(109,93,251,0.22);
        flex-shrink: 0;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 24px;
        letter-spacing: -0.01em;
        color: var(--text-primary);
        margin: 0;
        line-height: 1.25;
    }
    .hero-sub {
        color: var(--text-secondary);
        font-size: 13.5px;
        margin: 3px 0 0 0;
        letter-spacing: 0.01em;
    }
    .hero-right { display: flex; align-items: center; gap: 10px; position: relative; z-index: 1; flex-shrink: 0; }
    .session-chip {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        font-size: 11px;
        color: var(--text-muted);
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-weight: 600;
        padding-right: 14px;
        border-right: 1px solid var(--border-hair);
    }
    .session-chip span { color: var(--text-primary); font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 0; text-transform: none; margin-top: 2px; }
    .live-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #FB7185;
        background: var(--wicket-dim);
        border: 1px solid rgba(251,113,133,0.32);
        padding: 6px 12px 6px 9px;
        border-radius: 999px;
    }
    .live-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #FB7185;
        box-shadow: 0 0 0 0 rgba(251,113,133,0.45);
        animation: pulse-dot 1.8s infinite;
    }
    @keyframes pulse-dot {
        0%   { box-shadow: 0 0 0 0 rgba(251,113,133,0.4); }
        70%  { box-shadow: 0 0 0 7px rgba(251,113,133,0); }
        100% { box-shadow: 0 0 0 0 rgba(251,113,133,0); }
    }
    .hr-fade {
        height: 1px;
        border: none;
        margin: 18px 0 22px 0;
        background: linear-gradient(90deg, var(--border-hair) 0%, var(--border-hair-soft) 60%, transparent 100%);
    }

    /* ---------- Section labels ---------- */
    .section-label {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin: 4px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .section-label .tick { width: 3px; height: 14px; border-radius: 2px; background: var(--floodlight); display: inline-block; }

    /* ---------- Config panel ---------- */
    .config-panel {
        background: var(--bg-panel);
        border: 1px solid var(--border-hair);
        border-radius: 16px;
        padding: 18px 18px 4px 18px;
        box-shadow: var(--shadow-card);
    }
    .config-panel [data-testid="stVerticalBlock"] {
        gap: 0.65rem !important;
    }

    .mini-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
    }
    .mini-kpi {
        background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(248,250,252,0.92));
        border: 1px solid var(--border-hair);
        border-radius: 14px;
        padding: 13px 14px;
        box-shadow: var(--shadow-card);
    }
    .mini-kpi span {
        display: block;
        font-size: 11px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
    }
    .mini-kpi b {
        display: block;
        margin-top: 5px;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
        font-size: 18px;
    }

    /* ---------- Metric cards ---------- */
    .stat-card {
        background: var(--bg-panel);
        border: 1px solid var(--border-hair);
        border-left-width: 3px;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-card);
        transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }
    .stat-card.tone-floodlight { border-left-color: var(--floodlight); }
    .stat-card.tone-boundary   { border-left-color: var(--boundary); }
    .stat-card.tone-wicket     { border-left-color: var(--wicket); }
    .stat-card.tone-amber      { border-left-color: var(--amber); }

    .stat-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .stat-card-title {
        font-size: 12.5px;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .stat-card-badge {
        width: 26px; height: 26px;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px;
        border-radius: 8px;
        flex-shrink: 0;
    }
    .stat-card.tone-floodlight .stat-card-badge { background: var(--floodlight-dim); }
    .stat-card.tone-wicket .stat-card-badge { background: var(--wicket-dim); }
    .stat-card.tone-amber .stat-card-badge { background: var(--amber-dim); }
    
    .stat-card-value {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 26px;
        color: var(--text-primary);
        margin: 2px 0 6px 0;
    }
    .stat-card-foot {
        font-size: 12.5px;
        color: var(--text-muted);
        letter-spacing: 0.01em;
    }
    .stat-card-foot b { color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; font-weight: 600; }

    /* Forecast tiles */
    .forecast-tile {
        background: var(--bg-panel);
        border: 1px solid var(--border-hair);
        border-left-width: 3px;
        border-radius: 14px;
        padding: 16px 18px;
        text-align: left;
        box-shadow: var(--shadow-card);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .forecast-tile:hover { transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }
    .forecast-tile .fhead { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .forecast-tile .fdot { width: 8px; height: 8px; border-radius: 50%; }
    .forecast-tile .flabel { font-size: 12px; font-weight: 500; color: var(--text-secondary); letter-spacing: 0.02em; }
    .forecast-tile .fvalue {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 26px;
    }
    .forecast-tile.f-neutral  { border-left-color: var(--floodlight); }
    .forecast-tile.f-boundary { border-left-color: var(--boundary); }
    .forecast-tile.f-wicket   { border-left-color: var(--wicket); }
    .forecast-tile.f-neutral .fdot   { background: var(--floodlight); }
    .forecast-tile.f-boundary .fdot  { background: var(--boundary); }
    .forecast-tile.f-wicket .fdot    { background: var(--wicket); }
    .forecast-tile.f-neutral .fvalue  { color: var(--floodlight); }
    .forecast-tile.f-boundary .fvalue { color: var(--boundary); }
    .forecast-tile.f-wicket .fvalue   { color: var(--wicket); }

    .chart-shell {
        background: var(--bg-panel);
        border: 1px solid var(--border-hair);
        border-radius: 16px;
        padding: 16px;
        margin: 6px 0 18px 0;
        box-shadow: var(--shadow-card);
    }

    /* ---------- Win probability bar ---------- */
    .wp-wrap {
        margin-top: 4px; margin-bottom: 22px;
        background: var(--bg-panel);
        border: 1px solid var(--border-hair);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: var(--shadow-card);
    }
    .wp-labels { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; }
    .wp-labels .side { display: flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; }
    .wp-labels .dotmark { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .wp-labels .chasing { color: var(--boundary); }
    .wp-labels .chasing .dotmark { background: var(--boundary); }
    .wp-labels .defending { color: var(--wicket); }
    .wp-labels .defending .dotmark { background: var(--wicket); }
    .wp-labels .val { font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 700; color: var(--text-primary); margin-left: 6px; }
    .wp-track {
        position: relative;
        height: 10px;
        border-radius: 999px;
        background: var(--bg-panel-3);
        overflow: hidden;
    }
    .wp-fill {
        position: absolute; left: 0; top: 0; bottom: 0;
        background: linear-gradient(90deg, #22D3EE 0%, #A78BFA 52%, #FB7185 100%);
        border-radius: 999px;
    }

    /* ---------- Streamlit input overrides ---------- */
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSlider"] { color: var(--text-primary) !important; font-weight: 500; }
    
    /* Force readable text inside light selection controls */
    div[data-testid="stSelectbox"] * {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
    }
    
    /* Tabs Overrides */
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button *,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span {
        color: var(--text-secondary) !important;
        -webkit-text-fill-color: var(--text-secondary) !important;
        font-weight: 600 !important;
    }

    /* Popover menu options contrast alignments */
    div[data-baseweb="popover"] *,
    ul[role="listbox"] * {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        background-color: var(--bg-panel-2) !important;
    }

    div[data-testid="stNumberInput"] input {
        background-color: var(--bg-panel-3) !important;
        border: 1px solid var(--border-hair) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-size: 14px !important;
        min-height: 44px !important;
        padding-right: 42px !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
    }
    div[data-testid="stNumberInput"] > div {
        position: relative !important;
    }
    div[data-testid="stNumberInput"] > div::after {
        content: "+";
        position: absolute;
        right: 14px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #EAF8F3, #EAF2FF);
        border: 1px solid rgba(44,191,174,0.20);
        color: #0F766E;
        font-size: 16px;
        font-weight: 800;
        line-height: 1;
        pointer-events: none;
        box-shadow: 0 6px 14px rgba(15,23,42,0.06);
    }
    div[data-testid="stNumberInput"] input:focus {
        border-color: rgba(44,191,174,0.42) !important;
        box-shadow: 0 0 0 4px rgba(44,191,174,0.12), 0 10px 26px rgba(15,23,42,0.06) !important;
    }
    div[data-testid="stNumberInput"] button {
        display: none !important;
    }
    div[data-testid="stSelectbox"] > div > div {
        background-color: var(--bg-panel-3) !important;
        border: 1px solid var(--border-hair) !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: var(--floodlight) !important;
        box-shadow: 0 0 0 3px rgba(109,93,251,0.16) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background: linear-gradient(135deg, #0EA5E9, #6D5DFB) !important;
        border: 2px solid #FBFDF8 !important;
        box-shadow: 0 6px 16px rgba(109,93,251,0.24) !important;
    }
    div[data-testid="stSlider"] > div > div > div > div {
        background: linear-gradient(90deg, #0EA5E9, #6D5DFB) !important;
    }
    div[data-testid="stSlider"] div[data-testid="stTickBar"] {
        display: none !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div {
        background-color: #E2E8F0 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] {
        padding-top: 0.45rem !important;
        padding-bottom: 1rem !important;
    }
    label[data-testid="stWidgetLabel"] p {
        font-size: 12px !important;
        color: #1E293B !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        font-weight: 700;
    }

    /* ---------- Dataframe ---------- */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border-hair);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow-card);
    }

    /* ---------- Typography ---------- */
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.02em; color: var(--text-primary) !important; }

    /* ---------- Tabs (segmented controls layout framework) ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(251, 253, 248, 0.82);
        border: 1px solid var(--border-hair);
        border-radius: 12px;
        padding: 4px;
        width: fit-content;
        margin-bottom: 8px;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
    }
    .stTabs [data-baseweb="tab-list"] button {
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(251, 253, 248, 0.88) !important;
        border-radius: 9px;
        padding: 9px 20px;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        border-bottom: 1px solid rgba(15, 23, 42, 0.08) !important;
        font-size: 13.5px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"][aria-selected="false"] *,
    .stTabs [data-baseweb="tab"][aria-selected="false"] p,
    .stTabs [data-baseweb="tab"][aria-selected="false"] span,
    .stTabs [data-baseweb="tab"][aria-selected="false"] div,
    .stTabs button[aria-selected="false"] *,
    .stTabs button[aria-selected="false"] p,
    .stTabs button[aria-selected="false"] span,
    .stTabs button[aria-selected="false"] div {
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(224, 242, 254, 0.95) !important;
        border-color: rgba(14, 165, 233, 0.32) !important;
        color: #075985 !important;
        transform: translateY(-1px);
    }
    .stTabs [data-baseweb="tab"]:hover *,
    .stTabs [data-baseweb="tab"]:hover p,
    .stTabs [data-baseweb="tab"]:hover span,
    .stTabs [data-baseweb="tab"]:hover div {
        color: #075985 !important;
        -webkit-text-fill-color: #075985 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0EA5E9 0%, #6D5DFB 100%) !important;
        border-color: rgba(109, 93, 251, 0.48) !important;
        border-bottom-color: rgba(109, 93, 251, 0.48) !important;
        box-shadow: 0 10px 24px rgba(109, 93, 251, 0.26);
    }
    .stTabs button[aria-selected="true"] {
        background: linear-gradient(135deg, #0EA5E9 0%, #6D5DFB 100%) !important;
        border-color: rgba(109, 93, 251, 0.48) !important;
        border-bottom-color: rgba(109, 93, 251, 0.48) !important;
    }
    .stTabs button[aria-selected="false"] {
        background-color: rgba(251, 253, 248, 0.92) !important;
        border-color: rgba(15, 23, 42, 0.08) !important;
        border-bottom-color: rgba(15, 23, 42, 0.08) !important;
    }
    .stTabs [aria-selected="true"]:hover {
        background: linear-gradient(135deg, #0284C7 0%, #5B4BEA 100%) !important;
        border-color: rgba(91, 75, 234, 0.55) !important;
    }
    .stTabs [aria-selected="true"] *,
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div,
    .stTabs button[aria-selected="true"] *,
    .stTabs button[aria-selected="true"] p,
    .stTabs button[aria-selected="true"] span,
    .stTabs button[aria-selected="true"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ---------- Final tab + slider color overrides ---------- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(251, 253, 248, 0.86) !important;
        border-color: rgba(15, 23, 42, 0.08) !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
    }
    .stTabs button[aria-selected="false"],
    .stTabs [data-baseweb="tab"][aria-selected="false"] {
        background: rgba(251, 253, 248, 0.94) !important;
        border-color: rgba(15, 23, 42, 0.08) !important;
    }
    .stTabs button[aria-selected="false"] *,
    .stTabs [data-baseweb="tab"][aria-selected="false"] * {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        opacity: 1 !important;
    }
    .stTabs button[aria-selected="false"]:hover,
    .stTabs [data-baseweb="tab"][aria-selected="false"]:hover {
        background: #ECFEFF !important;
        border-color: rgba(14, 116, 144, 0.24) !important;
    }
    .stTabs button[aria-selected="false"]:hover *,
    .stTabs [data-baseweb="tab"][aria-selected="false"]:hover * {
        color: #0E7490 !important;
        -webkit-text-fill-color: #0E7490 !important;
    }
    .stTabs button[aria-selected="true"],
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0F766E 0%, #2563EB 100%) !important;
        border-color: rgba(15, 118, 110, 0.34) !important;
        border-bottom-color: rgba(15, 118, 110, 0.34) !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.20) !important;
    }
    .stTabs button[aria-selected="true"] *,
    .stTabs [data-baseweb="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
    }

    div[data-testid="stSlider"] [data-baseweb="slider"] {
        padding-top: 0.6rem !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div {
        background: #E2E8F0 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: #E2E8F0 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div {
        background: linear-gradient(90deg, #14B8A6 0%, #2563EB 100%) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background: #0F766E !important;
        border: 3px solid #FBFDF8 !important;
        box-shadow: 0 6px 16px rgba(15, 118, 110, 0.28) !important;
    }
    div[data-testid="stSlider"] [data-testid="stThumbValue"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="ThumbValue"] {
        background: #E0F2F1 !important;
        border: 1px solid rgba(15, 118, 110, 0.18) !important;
        box-shadow: 0 6px 14px rgba(15, 118, 110, 0.10) !important;
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
        border-radius: 7px !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="TickBar"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="InnerThumb"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="Thumb"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] div {
        -webkit-text-fill-color: inherit;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] span,
    div[data-testid="stSlider"] [data-baseweb="slider"] p {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background-color: rgb(0, 104, 201)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background: rgb(0, 104, 201)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(0, 104, 201)"] {
        background: #E0F2F1 !important;
        background-color: #E0F2F1 !important;
        border: 1px solid rgba(15, 118, 110, 0.18) !important;
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background-color: rgb(0, 104, 201)"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background: rgb(0, 104, 201)"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(0, 104, 201)"] * {
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-testid="stTickBarMin"],
    div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(255, 75, 75)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="#ff4b4b"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="255, 75, 75"] {
        background: #E0F2F1 !important;
        background-color: #E0F2F1 !important;
        border: 1px solid rgba(15, 118, 110, 0.18) !important;
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(255, 75, 75)"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="#ff4b4b"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="255, 75, 75"] * {
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [role="slider"]::before {
        background: #E0F2F1 !important;
        color: #0F766E !important;
    }
    div[data-testid="stSlider"] [role="slider"]::after {
        background: #E0F2F1 !important;
        color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [aria-valuenow] {
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [aria-valuenow] * {
        color: #0F766E !important;
        -webkit-text-fill-color: #0F766E !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background-color"] {
        border-radius: 999px !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div {
        background: linear-gradient(90deg, #14B8A6 0%, #2563EB 100%) !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div > div {
        background: linear-gradient(90deg, #14B8A6 0%, #2563EB 100%) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background: #0F766E !important;
        border-color: #FBFDF8 !important;
    }
    div[data-testid="stSlider"] [role="slider"] * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] span,
    div[data-testid="stSlider"] [data-baseweb="slider"] p,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="transform"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="position: absolute"] {
        color: transparent !important;
        -webkit-text-fill-color: transparent !important;
    }
    div[data-testid="stTabs"] button,
    div[data-testid="stTabs"] [role="tab"] {
        opacity: 1 !important;
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0F766E 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] *,
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .slider-readout {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin: -8px 0 12px 0;
        padding: 7px 11px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(236,253,245,0.96), rgba(219,234,254,0.92));
        border: 1px solid rgba(15,118,110,0.14);
        box-shadow: 0 10px 24px rgba(15,23,42,0.06);
        color: #0F766E;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 700;
    }
    .slider-readout span {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: linear-gradient(135deg, #14B8A6, #2563EB);
        box-shadow: 0 0 0 4px rgba(20,184,166,0.12);
    }

    /* ---------- Modern product-dashboard polish ---------- */
    .block-container {
        max-width: 1380px;
        padding-top: 1.35rem;
        padding-left: 2.25rem;
        padding-right: 2.25rem;
    }
    .hero-wrap,
    .config-panel,
    .stat-card,
    .forecast-tile,
    .wp-wrap,
    .chart-shell,
    .mini-kpi,
    div[data-testid="stDataFrame"] {
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border-color: rgba(15, 23, 42, 0.08) !important;
    }
    .hero-wrap {
        border-radius: 24px;
        padding: 26px 30px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.78), rgba(236,253,245,0.78)),
            radial-gradient(circle at 82% 16%, rgba(37,99,235,0.16), transparent 34%),
            radial-gradient(circle at 18% 24%, rgba(20,184,166,0.16), transparent 32%);
        box-shadow: 0 24px 70px rgba(15, 23, 42, 0.10);
    }
    .hero-title {
        font-size: 27px;
        letter-spacing: -0.035em;
    }
    .hero-sub {
        color: #475569;
        font-size: 14px;
    }
    .hero-badge {
        border-radius: 18px;
        background: linear-gradient(135deg, #0F766E 0%, #2563EB 100%);
        box-shadow: 0 16px 34px rgba(37, 99, 235, 0.22);
    }
    .live-pill {
        color: #0F766E;
        background: rgba(20, 184, 166, 0.12);
        border-color: rgba(15, 118, 110, 0.18);
    }
    .live-dot {
        background: #0F766E;
        box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.38);
    }
    .section-label {
        color: #1E293B;
        font-size: 12px;
        margin-bottom: 12px;
    }
    .section-label .tick {
        width: 4px;
        height: 16px;
        background: linear-gradient(180deg, #0F766E, #2563EB);
    }
    .config-panel,
    .stat-card,
    .forecast-tile,
    .wp-wrap,
    .chart-shell {
        background: rgba(251, 253, 248, 0.76) !important;
        border-radius: 20px;
        box-shadow: 0 18px 48px rgba(15, 23, 42, 0.075);
    }
    .stat-card,
    .forecast-tile {
        border-left-width: 0;
        position: relative;
        overflow: hidden;
    }
    .stat-card::before,
    .forecast-tile::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 5px;
        background: linear-gradient(180deg, #0F766E, #2563EB);
    }
    .stat-card.tone-wicket::before,
    .forecast-tile.f-wicket::before {
        background: linear-gradient(180deg, #F43F5E, #FB7185);
    }
    .stat-card.tone-amber::before {
        background: linear-gradient(180deg, #D97706, #FBBF24);
    }
    .forecast-tile.f-boundary::before {
        background: linear-gradient(180deg, #0891B2, #14B8A6);
    }
    .stat-card:hover,
    .forecast-tile:hover,
    .mini-kpi:hover {
        transform: translateY(-3px);
        box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
    }
    .stat-card-badge {
        border-radius: 10px;
        background: rgba(15, 118, 110, 0.10) !important;
    }
    .stat-card-value,
    .forecast-tile .fvalue {
        letter-spacing: -0.03em;
    }
    .mini-kpi {
        background: linear-gradient(145deg, rgba(255,255,255,0.88), rgba(236,253,245,0.74));
        border-radius: 18px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .mini-kpi b {
        color: #0F766E;
    }
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background: rgba(255,255,255,0.78) !important;
        border-color: rgba(15, 23, 42, 0.10) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05) !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-size: 11.5px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        border-radius: 999px !important;
        padding: 5px !important;
        background: rgba(255,255,255,0.58) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }
    .stTabs button,
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px !important;
        padding: 9px 18px !important;
    }
    .wp-track {
        height: 12px;
        background: #E2E8F0;
    }
    .wp-fill {
        background: linear-gradient(90deg, #0F766E 0%, #14B8A6 45%, #2563EB 100%);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        box-shadow: 0 18px 48px rgba(15, 23, 42, 0.075);
    }

    /* ---------- Vibrant light theme finish ---------- */
    .stApp {
        background:
            radial-gradient(circle at 8% 10%, rgba(20,184,166,0.18), transparent 28%),
            radial-gradient(circle at 92% 8%, rgba(37,99,235,0.16), transparent 28%),
            radial-gradient(circle at 72% 86%, rgba(168,85,247,0.12), transparent 30%),
            linear-gradient(135deg, #FFFDF5 0%, #F1FAF4 46%, #EEF6FF 100%) !important;
    }
    .hero-wrap {
        background:
            linear-gradient(135deg, rgba(255,255,255,0.74), rgba(236,253,245,0.80)),
            radial-gradient(circle at 14% 20%, rgba(20,184,166,0.20), transparent 30%),
            radial-gradient(circle at 82% 18%, rgba(37,99,235,0.18), transparent 36%),
            radial-gradient(circle at 66% 92%, rgba(168,85,247,0.10), transparent 34%);
    }
    .hero-wrap::before {
        background: radial-gradient(ellipse at top right, rgba(14,165,233,0.20) 0%, rgba(14,165,233,0) 68%);
    }
    .hero-wrap::after {
        border-color: rgba(37,99,235,0.13);
        box-shadow: inset 0 0 52px rgba(20,184,166,0.16);
    }
    .config-panel,
    .stat-card,
    .forecast-tile,
    .wp-wrap,
    .chart-shell {
        background:
            linear-gradient(145deg, rgba(255,255,255,0.82), rgba(246,253,247,0.74)) !important;
        border-color: rgba(15,118,110,0.10) !important;
    }
    .mini-kpi {
        background:
            linear-gradient(145deg, rgba(255,255,255,0.88), rgba(239,246,255,0.78)) !important;
        border-color: rgba(37,99,235,0.10) !important;
    }
    .stat-card.tone-floodlight::before,
    .forecast-tile.f-neutral::before {
        background: linear-gradient(180deg, #2563EB, #A855F7);
    }
    .section-label .tick {
        background: linear-gradient(180deg, #14B8A6, #2563EB, #A855F7);
    }
    .stTabs button[aria-selected="true"],
    .stTabs [data-baseweb="tab"][aria-selected="true"],
    div[data-testid="stTabs"] button[aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #14B8A6 0%, #2563EB 58%, #7C3AED 100%) !important;
        box-shadow: 0 12px 28px rgba(37,99,235,0.22) !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div,
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: #DDEFE1 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div,
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div > div > div {
        background: linear-gradient(90deg, #8DDCCB 0%, #7DB8F5 100%) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background: #2CBFAE !important;
        border-color: #F8FCF5 !important;
        box-shadow: 0 8px 18px rgba(44,191,174,0.20) !important;
    }
    div[data-testid="stSlider"] [data-testid="stThumbValue"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="ThumbValue"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background-color: rgb(0, 104, 201)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(0, 104, 201)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="background-color: rgb(20, 184, 166)"],
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(20, 184, 166)"] {
        background: #EAF8F3 !important;
        background-color: #EAF8F3 !important;
        border: 1px solid rgba(44,191,174,0.24) !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        box-shadow: 0 6px 14px rgba(15,23,42,0.08) !important;
    }
    div[data-testid="stSlider"] [data-testid="stThumbValue"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [class*="ThumbValue"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(0, 104, 201)"] *,
    div[data-testid="stSlider"] [data-baseweb="slider"] [style*="rgb(20, 184, 166)"] * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }
    .slider-readout {
        background: linear-gradient(135deg, rgba(250,255,250,0.98), rgba(234,248,243,0.96));
        color: #0F172A;
        border-color: rgba(44,191,174,0.18);
    }
    .slider-readout span {
        background: linear-gradient(135deg, #8DDCCB, #7DB8F5);
    }
    .wp-fill {
        background: linear-gradient(90deg, #14B8A6 0%, #2563EB 60%, #7C3AED 100%);
    }

    /* ---------- Final UX refinements ---------- */
    * {
        scrollbar-width: thin;
        scrollbar-color: rgba(15,118,110,0.36) transparent;
    }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, rgba(20,184,166,0.42), rgba(37,99,235,0.32));
        border-radius: 999px;
        border: 3px solid transparent;
        background-clip: padding-box;
    }
    .block-container > div {
        animation: fade-slide-in 0.42s ease both;
    }
    @keyframes fade-slide-in {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    button,
    [role="button"],
    div[data-testid="stSelectbox"],
    div[data-testid="stNumberInput"] {
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }
    div[data-testid="stSelectbox"]:hover,
    div[data-testid="stNumberInput"]:hover {
        transform: translateY(-1px);
    }
    div[data-testid="stNumberInput"]:hover > div::after {
        background: linear-gradient(135deg, #DDF7EE, #DBEAFE);
        transform: translateY(-50%) scale(1.04);
    }
    div[data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.72);
        border-radius: 18px;
    }
    div[data-testid="stAlert"] {
        box-shadow: 0 14px 38px rgba(15,23,42,0.075);
    }
    div[data-testid="stMarkdownContainer"] a {
        color: #0F766E !important;
        text-decoration-color: rgba(15,118,110,0.32) !important;
        text-underline-offset: 3px;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        position: sticky;
        top: 8px;
        z-index: 20;
    }
    .forecast-tile .fhead,
    .stat-card-head {
        min-height: 28px;
    }
    .chart-shell {
        padding: 20px;
    }
    .hr-fade {
        margin: 22px 0 24px 0;
        background: linear-gradient(90deg, transparent 0%, rgba(15,118,110,0.18) 18%, rgba(37,99,235,0.18) 70%, transparent 100%);
    }
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .hero-wrap {
            flex-direction: column;
            align-items: flex-start;
            padding: 22px;
        }
        .hero-right {
            width: 100%;
            justify-content: space-between;
        }
        .mini-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .stTabs [data-baseweb="tab-list"] {
            width: 100%;
            overflow-x: auto;
        }
    }
    @media (max-width: 560px) {
        .mini-strip {
            grid-template-columns: 1fr;
        }
        .hero-title {
            font-size: 22px;
        }
        .session-chip {
            align-items: flex-start;
        }
    }

    /* ---------- Alerts ---------- */
    div[data-testid="stAlert"] { border-radius: 12px; background-color: var(--bg-panel); border: 1px solid var(--border-hair); }
</style>
""", unsafe_allow_html=True)

MODEL_PATH = os.path.join("data", "2_processed", "matchup_model.pkl")
ENCODER_PATH = os.path.join("data", "2_processed", "encoders.pkl")

def get_snowflake_connection():
    """Dynamically establishes a connection using local .env or Streamlit Cloud Secrets"""
    try:
        if "SF_USER" in st.secrets and st.secrets["SF_USER"]:
            return snowflake.connector.connect(
                user=st.secrets["SF_USER"],
                password=st.secrets["SF_PASSWORD"],
                account=st.secrets["SF_ACCOUNT"],
                warehouse=st.secrets["SF_WAREHOUSE"],
                database=st.secrets["SF_DATABASE"],
                schema=st.secrets["SF_SCHEMA"]
            )
    except Exception:
        pass

    return snowflake.connector.connect(
        user=os.getenv("SF_USER"),
        password=os.getenv("SF_PASSWORD"),
        account=os.getenv("SF_ACCOUNT"),
        warehouse=os.getenv("SF_WAREHOUSE"),
        database=os.getenv("SF_DATABASE"),
        schema=os.getenv("SF_SCHEMA")
    )

@st.cache_resource
def load_ml_objects():
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        with open(MODEL_PATH, "rb") as m_f:
            model = pickle.load(m_f)
        with open(ENCODER_PATH, "rb") as e_f:
            encoders = pickle.load(e_f)
        return model, encoders
    return None, None

@st.cache_data(ttl=7200)
def get_team_rosters():
    ctx = get_snowflake_connection()
    recent_matches_query = "SELECT DISTINCT MATCH_ID FROM RAW_DELIVERIES ORDER BY MATCH_ID DESC LIMIT 25"
    recent_matches = pd.read_sql(recent_matches_query, ctx)['MATCH_ID'].tolist()
    match_id_string = ','.join(map(str, recent_matches))

    batting_query = f"SELECT DISTINCT BATTING_TEAM as TEAM, STRIKER as PLAYER FROM RAW_DELIVERIES WHERE MATCH_ID IN ({match_id_string})"
    bowling_query = f"SELECT DISTINCT BOWLING_TEAM as TEAM, BOWLER as PLAYER FROM RAW_DELIVERIES WHERE MATCH_ID IN ({match_id_string})"

    df_batters = pd.read_sql(batting_query, ctx)
    df_batters['ROLE'] = 'batter'
    df_bowlers = pd.read_sql(bowling_query, ctx)
    df_bowlers['ROLE'] = 'bowler'

    df_rosters = pd.concat([df_batters, df_bowlers], ignore_index=True)
    ctx.close()
    return df_rosters

@st.cache_data(ttl=7200)
def get_detailed_stats(batter, bowler):
    ctx = get_snowflake_connection()
    h2h_query = "SELECT COALESCE(SUM(RUNS_OFF_BAT), 0) as TOTAL_RUNS, COUNT(BALL) as TOTAL_BALLS, COALESCE(SUM(CASE WHEN PLAYER_DISMISSED IS NOT NULL AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as TOTAL_WICKETS FROM RAW_DELIVERIES WHERE STRIKER = %s AND BOWLER = %s"
    df_h2h = pd.read_sql(h2h_query, ctx, params=(batter, bowler)).iloc[0]

    bat_query = "SELECT COALESCE(SUM(RUNS_OFF_BAT), 0)/2 as RUNS, COUNT(BALL)/2 as BALLS, COUNT(DISTINCT MATCH_ID) as TOTAL_INNINGS, COALESCE(SUM(CASE WHEN PLAYER_DISMISSED = %s AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0)/2 as TOTAL_DISMISSALS FROM RAW_DELIVERIES WHERE STRIKER = %s"
    df_bat = pd.read_sql(bat_query, ctx, params=(batter, batter)).iloc[0]

    bowl_query = "SELECT COALESCE(SUM(RUNS_OFF_BAT), 0)/2 as RUNS_CONCEDED, COUNT(BALL)/2 as BALLS_BOWLED, COALESCE(SUM(CASE WHEN PLAYER_DISMISSED IS NOT NULL AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0)/2 as WICKETS_TAKEN FROM RAW_DELIVERIES WHERE BOWLER = %s"
    df_bowl = pd.read_sql(bowl_query, ctx, params=(bowler,)).iloc[0]
    ctx.close()
    return df_h2h, df_bat, df_bowl

@st.cache_data(ttl=7200)
def fetch_knn_candidate_pool(balls_left):
    ctx = get_snowflake_connection()
    query = """
        SELECT BALLS_REMAINING, RUNS_NEEDED, CURRENT_WICKETS_LOST, REQUIRED_RUN_RATE, CHASE_WON
        FROM ANALYTICAL_MATCHUP_FEATURES
        WHERE BALLS_REMAINING BETWEEN %s AND %s
    """
    df = pd.read_sql(query, ctx, params=(max(balls_left - 15, 0), balls_left + 15))
    ctx.close()
    return df

def calculate_historical_win_percentage(balls_left, wickets_lost, current_score, target_score):
    runs_needed = target_score - current_score
    if runs_needed <= 0: return 100.0
    if balls_left <= 0: return 0.0
    if wickets_lost >= 10: return 0.0

    req_run_rate = (runs_needed / balls_left) * 6
    df_features = fetch_knn_candidate_pool(balls_left)

    if df_features.empty:
        base_prob = 50.0 + ((10 - wickets_lost) * 4.5) - (req_run_rate * 4.0) + (balls_left * 0.1)
        return max(min(base_prob, 95.0), 5.0)

    b_remain_max = df_features['BALLS_REMAINING'].max() or 1
    runs_need_max = df_features['RUNS_NEEDED'].max() or 1
    rrr_max = df_features['REQUIRED_RUN_RATE'].max() or 1

    df_features['dist'] = np.sqrt(
        ((df_features['BALLS_REMAINING']/b_remain_max - balls_left/b_remain_max) * 1.0) ** 2 +
        ((df_features['RUNS_NEEDED']/runs_need_max - runs_needed/runs_need_max) * 1.5) ** 2 +
        ((df_features['CURRENT_WICKETS_LOST']/10.0 - wickets_lost/10.0) * 3.5) ** 2 +
        ((df_features['REQUIRED_RUN_RATE']/rrr_max - req_run_rate/rrr_max) * 2.0) ** 2
    )

    k_neighbors = df_features.nsmallest(120, 'dist')
    calibrated_pct = (k_neighbors['CHASE_WON'].mean() * 100) * ((10 - wickets_lost) / 10.0) ** 0.45
    return max(min(calibrated_pct, 98.0), 2.0)

def render_event_probability_chart(probabilities):
    df_events = pd.DataFrame({
        "Event": ["Single / Dot", "Boundary", "Dismissal Risk"],
        "Probability": [probabilities[0] * 100, probabilities[1] * 100, probabilities[2] * 100],
        "Color": ["#2563EB", "#0F766E", "#F43F5E"]
    })
    chart = (
        alt.Chart(df_events)
        .mark_bar(cornerRadiusTopRight=10, cornerRadiusBottomRight=10, size=26)
        .encode(
            x=alt.X(
                "Probability:Q",
                title=None,
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(format=".0f", grid=True, labelPadding=8)
            ),
            y=alt.Y("Event:N", title=None, sort=None, axis=alt.Axis(labelPadding=12)),
            color=alt.Color("Event:N", scale=alt.Scale(range=df_events["Color"].tolist()), legend=None),
            tooltip=[alt.Tooltip("Event:N"), alt.Tooltip("Probability:Q", format=".1f")]
        )
        .properties(height=150, background="transparent")
        .configure_view(strokeWidth=0, fill="transparent")
        .configure_axis(
            gridColor="#E6EEE6",
            labelColor="#475569",
            domain=False,
            tickColor="#CBD5E1",
            labelFont="Inter",
            titleFont="Inter"
        )
    )
    st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

def render_matchup_threat_chart(df_analysis, batter_name):
    chart_df = df_analysis[[
        "Active Opposing Bowler",
        f"{batter_name} Wicket Danger %",
        f"{batter_name} Boundary Leak %"
    ]].melt("Active Opposing Bowler", var_name="Signal", value_name="Percent")
    chart_df["Signal"] = chart_df["Signal"].str.replace(f"{batter_name} ", "", regex=False).str.replace(" %", "", regex=False)

    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=7, cornerRadiusTopRight=7)
        .encode(
            x=alt.X(
                "Active Opposing Bowler:N",
                title=None,
                sort="-y",
                axis=alt.Axis(labelAngle=-35, labelLimit=140, labelPadding=10)
            ),
            y=alt.Y(
                "Percent:Q",
                title="Predicted probability (%)",
                axis=alt.Axis(grid=True, labelPadding=8)
            ),
            color=alt.Color(
                "Signal:N",
                scale=alt.Scale(range=["#F43F5E", "#0F766E"]),
                legend=alt.Legend(orient="top", title=None, symbolType="square")
            ),
            xOffset="Signal:N",
            tooltip=[
                alt.Tooltip("Active Opposing Bowler:N", title="Bowler"),
                alt.Tooltip("Signal:N"),
                alt.Tooltip("Percent:Q", format=".1f")
            ]
        )
        .properties(height=360, background="transparent")
        .configure_view(strokeWidth=0, fill="transparent")
        .configure_axis(
            gridColor="#E6EEE6",
            labelColor="#475569",
            titleColor="#334155",
            domain=False,
            tickColor="#CBD5E1",
            labelFont="Inter",
            titleFont="Inter"
        )
        .configure_legend(labelColor="#334155", labelFont="Inter")
    )
    st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

# --- APP LAYOUT RUNNER ---
model, encoders = load_ml_objects()
df_rosters = get_team_rosters()

if model is None or df_rosters.empty:
    st.error("❌ Critical system initialization files missing database context mappings.")
else:
    all_batters_global = sorted(df_rosters[df_rosters['ROLE'] == 'batter']['PLAYER'].unique())
    all_bowlers_global = sorted(df_rosters[df_rosters['ROLE'] == 'bowler']['PLAYER'].unique())
    all_teams = sorted(df_rosters['TEAM'].unique())

    st.markdown("""
        <div class="hero-wrap">
            <div class="hero-left">
                <div class="hero-badge">🏏</div>
                <div>
                    <p class="hero-title">IPL Strategy Engine</p>
                    <p class="hero-sub">Predictive operations center for ball-by-ball matchup intelligence</p>
                </div>
            </div>
            <div class="hero-right">
                <div class="session-chip">Model Build<span>v2.3-knn</span></div>
                <span class="live-pill"><span class="live-dot"></span>LIVE MODEL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊  Live Simulation Deck", "🛡️  Franchise Matchup Matrix"])

    with tab1:
        c_setup1, c_setup2 = st.columns([1, 2], gap="large")
        with c_setup1:
            st.markdown('<p class="section-label"><span class="tick"></span>Match Parameters</p>', unsafe_allow_html=True)
            st.markdown('<div class="config-panel">', unsafe_allow_html=True)
            sim_batter = st.selectbox("Active Striker", all_batters_global, index=0)
            sim_bowler = st.selectbox("Active Bowler", all_bowlers_global, index=0)
            current_score = st.number_input("Current Runs Scored", min_value=0, value=120)
            wickets_down = st.number_input("Wickets Lost", min_value=0, max_value=9, value=3, step=1)
            overs_completed = st.number_input("Overs Completed", min_value=0.0, max_value=19.5, value=15.0, step=0.1, format="%.1f")
            target_to_chase = st.number_input("Target to Chase", min_value=0, value=160)
            st.markdown('</div>', unsafe_allow_html=True)

        with c_setup2:
            st.markdown('<p class="section-label"><span class="tick"></span>Live In-Game Metrics</p>', unsafe_allow_html=True)
            h2h, bat_p, bowl_p = get_detailed_stats(sim_batter, sim_bowler)

            k_prof1, k_prof2 = st.columns(2)
            with k_prof1:
                b_sr = (bat_p['RUNS'] / bat_p['BALLS']) * 100 if bat_p['BALLS'] > 0 else 0
                b_avg = bat_p['RUNS'] / int(bat_p['TOTAL_DISMISSALS']) if int(bat_p['TOTAL_DISMISSALS']) > 0 else bat_p['RUNS'] / max(int(bat_p['TOTAL_INNINGS']), 1)
                st.markdown(f"""
                    <div class="stat-card tone-floodlight">
                        <div class="stat-card-head">
                            <span class="stat-card-title">{sim_batter} · Career</span>
                            <span class="stat-card-badge">🏏</span>
                        </div>
                        <p class="stat-card-value stat-mono">{int(bat_p['RUNS'])} <span style="font-size:14px;color:var(--text-muted);">runs</span></p>
                        <p class="stat-card-foot">Avg <b>{b_avg:.2f}</b> &nbsp;·&nbsp; SR <b>{b_sr:.1f}</b> &nbsp;·&nbsp; Inn <b>{int(bat_p['TOTAL_INNINGS'])}</b></p>
                    </div>
                """, unsafe_allow_html=True)
            with k_prof2:
                bw_econ = (bowl_p['RUNS_CONCEDED'] / bowl_p['BALLS_BOWLED']) * 6 if bowl_p['BALLS_BOWLED'] > 0 else 0
                bw_wickets = int(bowl_p['WICKETS_TAKEN'])
                bw_avg = bowl_p['RUNS_CONCEDED'] / bw_wickets if bw_wickets > 0 else np.nan
                avg_str = f"{bw_avg:.2f}" if not np.isnan(bw_avg) else "N/A"
                st.markdown(f"""
                    <div class="stat-card tone-wicket">
                        <div class="stat-card-head">
                            <span class="stat-card-title">{sim_bowler} · Career</span>
                            <span class="stat-card-badge">🎯</span>
                        </div>
                        <p class="stat-card-value stat-mono">{bw_wickets} <span style="font-size:14px;color:var(--text-muted);">wickets</span></p>
                        <p class="stat-card-foot">Econ <b>{bw_econ:.2f}</b> &nbsp;·&nbsp; Avg <b>{avg_str}</b> &nbsp;·&nbsp; Balls <b>{int(bowl_p['BALLS_BOWLED'])}</b></p>
                    </div>
                """, unsafe_allow_html=True)

            # Restored Head-to-Head Statistics Panel Block
            h2h_runs = int(h2h['TOTAL_RUNS'])/2
            h2h_balls = int(h2h['TOTAL_BALLS'])/2
            h2h_wickets = int(h2h['TOTAL_WICKETS'])/2
            h2h_sr = (h2h_runs / h2h_balls) * 100 if h2h_balls > 0 else 0.0

            st.markdown(f"""
                <div class="stat-card tone-amber">
                    <div class="stat-card-head">
                        <span class="stat-card-title">Head-to-Head History · {sim_batter} vs {sim_bowler}</span>
                        <span class="stat-card-badge">⚔️</span>
                    </div>
                    <p class="stat-card-value stat-mono">{h2h_runs} <span style="font-size:14px;color:var(--text-muted);">runs off</span> {h2h_balls} <span style="font-size:14px;color:var(--text-muted);">balls</span></p>
                    <p class="stat-card-foot">Matchup Dismissals <b>{h2h_wickets}</b> &nbsp;·&nbsp; Matchup SR <b>{h2h_sr:.1f}</b></p>
                </div>
            """, unsafe_allow_html=True)

            total_balls_bowled = int(overs_completed) * 6 + int((overs_completed - int(overs_completed)) * 10)
            balls_remaining = max(120 - total_balls_bowled, 0)
            crr = (current_score / total_balls_bowled) * 6 if total_balls_bowled > 0 else 0.0
            rrr = ((target_to_chase - current_score) / balls_remaining) * 6 if target_to_chase > 0 and balls_remaining > 0 else 0.0
            runs_needed = max(target_to_chase - current_score, 0)

            st.markdown(f"""
                <div class="mini-strip">
                    <div class="mini-kpi"><span>Balls Left</span><b>{balls_remaining}</b></div>
                    <div class="mini-kpi"><span>Runs Needed</span><b>{runs_needed}</b></div>
                    <div class="mini-kpi"><span>Current RR</span><b>{crr:.2f}</b></div>
                    <div class="mini-kpi"><span>Required RR</span><b>{rrr:.2f}</b></div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown('<p class="section-label"><span class="tick"></span>Win Probability</p>', unsafe_allow_html=True)
            win_pct = calculate_historical_win_percentage(balls_remaining, wickets_down, current_score, target_to_chase)

            st.markdown(f"""
                <div class="wp-wrap">
                    <div class="wp-labels">
                        <span class="side chasing"><span class="dotmark"></span>Chasing<span class="val">{win_pct:.1f}%</span></span>
                        <span class="side defending">Defending<span class="val">{(100.0 - win_pct):.1f}%</span><span class="dotmark"></span></span>
                    </div>
                    <div class="wp-track">
                        <div class="wp-fill" style="width:{win_pct:.1f}%;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            try:
                bat_enc = encoders['striker'].transform([sim_batter])[0]
                bow_enc = encoders['bowler'].transform([sim_bowler])[0]
                v = np.array([[bat_enc, bow_enc, balls_remaining, wickets_down, crr, rrr]])
                ml_p = model.predict_proba(v)[0]

                st.markdown('<p class="section-label"><span class="tick"></span>Next-Ball Event Forecast</p>', unsafe_allow_html=True)
                pm1, pm2, pm3 = st.columns(3)
                with pm1:
                    st.markdown(f'<div class="forecast-tile f-neutral"><div class="fhead"><span class="fdot"></span><span class="flabel">Single / Dot</span></div><div class="fvalue">{ml_p[0]*100:.1f}%</div></div>', unsafe_allow_html=True)
                with pm2:
                    st.markdown(f'<div class="forecast-tile f-boundary"><div class="fhead"><span class="fdot"></span><span class="flabel">Boundary</span></div><div class="fvalue">{ml_p[1]*100:.1f}%</div></div>', unsafe_allow_html=True)
                with pm3:
                    st.markdown(f'<div class="forecast-tile f-wicket"><div class="fhead"><span class="fdot"></span><span class="flabel">Dismissal Risk</span></div><div class="fvalue">{ml_p[2]*100:.1f}%</div></div>', unsafe_allow_html=True)
                render_event_probability_chart(ml_p)
            except Exception as ml_err:
                st.error(f"⚠️ ML Prediction Error: {str(ml_err)}")

    with tab2:
        st.markdown('<p class="section-label"><span class="tick"></span>Opposing Franchise Matchup Matrix</p>', unsafe_allow_html=True)
        t_col1, t_col2 = st.columns(2)
        with t_col1: my_team = st.selectbox("Your Analytics Context Franchise", all_teams, index=0)
        with t_col2: opposing_team = st.selectbox("Target Opponent Context", [t for t in all_teams if t != my_team], index=0)

        available_batters = sorted(df_rosters[(df_rosters['TEAM'] == my_team) & (df_rosters['ROLE'] == 'batter')]['PLAYER'].unique())
        available_bowlers = sorted(df_rosters[(df_rosters['TEAM'] == opposing_team) & (df_rosters['ROLE'] == 'bowler')]['PLAYER'].unique())

        p_col1, p_col2 = st.columns(2)
        with p_col1: batter_1 = st.selectbox("Franchise Batter A", available_batters, index=0)
        with p_col2: batter_2 = st.selectbox("Franchise Batter B", [b for b in available_batters if b != batter_1], index=min(1, len(available_batters)-1))

        st.markdown('<hr class="hr-fade" />', unsafe_allow_html=True)
        analysis_records = []
        for bowler in available_bowlers:
            try:
                h2h_1, _, bowl_prof = get_detailed_stats(batter_1, bowler)
                b_enc = encoders['bowler'].transform([bowler])[0]
                b1_enc = encoders['striker'].transform([batter_1])[0]
                v1 = np.array([[b1_enc, b_enc, 30, 3, 7.5, 9.0]])
                p1 = model.predict_proba(v1)[0]

                b2_enc = encoders['striker'].transform([batter_2])[0]
                v2 = np.array([[b2_enc, b_enc, 30, 3, 7.5, 9.0]])
                p2 = model.predict_proba(v2)[0]

                analysis_records.append({
                    "Active Opposing Bowler": bowler,
                    f"{batter_1} Wicket Danger %": round(p1[2] * 100, 1),
                    f"{batter_1} Boundary Leak %": round(p1[1] * 100, 1),
                    f"{batter_2} Wicket Danger %": round(p2[2] * 100, 1),
                    f"{batter_2} Boundary Leak %": round(p2[1] * 100, 1),
                    "Total Wickets Taken": int(bowl_prof['WICKETS_TAKEN'])
                })
            except Exception: continue

        if analysis_records:
            df_analysis = pd.DataFrame(analysis_records).sort_values(by=f"{batter_1} Wicket Danger %", ascending=False).reset_index(drop=True)
            danger_cols = [f"{batter_1} Wicket Danger %", f"{batter_2} Wicket Danger %"]
            leak_cols = [f"{batter_1} Boundary Leak %", f"{batter_2} Boundary Leak %"]
            try:
                styled_df = (
                    df_analysis.style
                    .background_gradient(subset=danger_cols, cmap="Reds", vmin=0, vmax=60)
                    .background_gradient(subset=leak_cols, cmap="Greens", vmin=0, vmax=30)
                    .format({c: "{:.1f}%" for c in danger_cols + leak_cols})
                    .set_properties(**{"font-family": "Inter, sans-serif", "font-size": "13px"})
                )
                st.dataframe(styled_df, use_container_width=True)
            except ImportError:
                # matplotlib not available for background_gradient — fall back to plain table
                st.dataframe(df_analysis, use_container_width=True)
            st.markdown('<p class="section-label"><span class="tick"></span>Visual Matchup Threat Spectrum</p>', unsafe_allow_html=True)
            render_matchup_threat_chart(df_analysis, batter_1)
