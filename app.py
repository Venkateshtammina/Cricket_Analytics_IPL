import os
import snowflake.connector
import pandas as pd
import streamlit as st
import pickle
import numpy as np
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
# Design tokens: "analyst desk" — a clean, light, professional dashboard
# theme. Soft neutral gray canvas, white cards with hairline borders and
# quiet shadows, and a restrained professional palette (deep blue, forest
# green, brick red) rather than neon broadcast colors. Numbers still render
# in a monospace face for a data-desk feel, kept subtle rather than loud.
# ---------------------------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-canvas: #F3F5F9;
        --bg-panel: #FFFFFF;
        --bg-panel-2: #FFFFFF;
        --bg-panel-3: #F3F5F9;
        --border-hair: #E1E5EE;
        --border-hair-soft: #ECEFF5;
        --text-primary: #10192E;
        --text-secondary: #5C6579;
        --text-muted: #8A93A6;
        --floodlight: #1C5FCC;
        --floodlight-dim: rgba(28, 95, 204, 0.08);
        --boundary: #178A4C;
        --boundary-dim: rgba(23, 138, 76, 0.08);
        --wicket: #D33A3A;
        --wicket-dim: rgba(211, 58, 58, 0.07);
        --amber: #B4690E;
        --shadow-card: 0 1px 2px rgba(16,24,45,0.04), 0 6px 16px rgba(16,24,45,0.06);
        --shadow-card-hover: 0 4px 8px rgba(16,24,45,0.05), 0 12px 24px rgba(16,24,45,0.09);
    }

    html, body, .stApp {
        background: var(--bg-canvas);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }

    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #123B85 0%, var(--floodlight) 45%, #4E8FE0 100%);
        z-index: 999;
    }

    /* Numeric / scoreboard figures */
    .stat-mono { font-family: 'JetBrains Mono', monospace; }

    /* ---------- Sidebar ---------- */
    div[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border-hair);
    }

    /* Add breathing room around the whole app */
    .block-container { padding-top: 1.6rem; }

    /* ---------- Hero header ---------- */
    .hero-wrap {
        position: relative;
        background: #FFFFFF;
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
        background: radial-gradient(ellipse at top right, rgba(28,95,204,0.06) 0%, rgba(28,95,204,0) 70%);
        pointer-events: none;
    }
    .hero-left { display: flex; align-items: center; gap: 16px; position: relative; z-index: 1; }
    .hero-badge {
        width: 52px; height: 52px;
        border-radius: 14px;
        background: linear-gradient(145deg, #123B85 0%, var(--floodlight) 100%);
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
        box-shadow: 0 6px 16px rgba(28,95,204,0.28);
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
        color: var(--wicket);
        background: var(--wicket-dim);
        border: 1px solid rgba(211,58,58,0.22);
        padding: 6px 12px 6px 9px;
        border-radius: 999px;
    }
    .live-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--wicket);
        box-shadow: 0 0 0 0 rgba(211,58,58,0.45);
        animation: pulse-dot 1.8s infinite;
    }
    @keyframes pulse-dot {
        0%   { box-shadow: 0 0 0 0 rgba(211,58,58,0.4); }
        70%  { box-shadow: 0 0 0 7px rgba(211,58,58,0); }
        100% { box-shadow: 0 0 0 0 rgba(211,58,58,0); }
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
        background: #FFFFFF;
        border: 1px solid var(--border-hair);
        border-radius: 16px;
        padding: 20px 20px 8px 20px;
        box-shadow: var(--shadow-card);
    }

    /* ---------- Metric cards ---------- */
    .stat-card {
        background: #FFFFFF;
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
        background: #FFFFFF;
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

    /* ---------- Win probability bar ---------- */
    .wp-wrap {
        margin-top: 4px; margin-bottom: 22px;
        background: #FFFFFF;
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
        background: var(--wicket-dim);
        overflow: hidden;
    }
    .wp-fill {
        position: absolute; left: 0; top: 0; bottom: 0;
        background: linear-gradient(90deg, #229356 0%, var(--boundary) 100%);
        border-radius: 999px;
    }

    /* ---------- Streamlit input overrides ---------- */
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] div,
    div[data-testid="stSlider"] { color: var(--text-primary); }
    div[data-testid="stNumberInput"] input {
        background-color: var(--bg-panel-3) !important;
        border: 1px solid var(--border-hair) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stNumberInput"] button {
        background-color: var(--bg-panel-3) !important;
        border: 1px solid var(--border-hair) !important;
    }
    div[data-testid="stSelectbox"] > div > div {
        background-color: var(--bg-panel-3) !important;
        border: 1px solid var(--border-hair) !important;
        border-radius: 8px !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: var(--floodlight) !important;
        box-shadow: 0 0 0 3px rgba(28,95,204,0.12) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background-color: var(--floodlight) !important;
        box-shadow: 0 0 0 4px rgba(28,95,204,0.14) !important;
    }
    div[data-testid="stSlider"] > div > div > div > div {
        background-color: var(--floodlight) !important;
    }
    label[data-testid="stWidgetLabel"] p {
        font-size: 12.5px !important;
        color: var(--text-secondary) !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        font-weight: 600;
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

    /* ---------- Tabs (segmented control) ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #EBEEF4;
        border: 1px solid var(--border-hair);
        border-radius: 12px;
        padding: 4px;
        width: fit-content;
        margin-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-secondary);
        border-radius: 9px;
        padding: 9px 20px;
        border: none;
        font-size: 13.5px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(16,24,45,0.06), 0 2px 6px rgba(16,24,45,0.08);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ---------- Alerts ---------- */
    div[data-testid="stAlert"] { border-radius: 12px; }
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

    bat_query = "SELECT COALESCE(SUM(RUNS_OFF_BAT), 0) as RUNS, COUNT(BALL) as BALLS, COUNT(DISTINCT MATCH_ID) as TOTAL_INNINGS, COALESCE(SUM(CASE WHEN PLAYER_DISMISSED = %s AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as TOTAL_DISMISSALS FROM RAW_DELIVERIES WHERE STRIKER = %s"
    df_bat = pd.read_sql(bat_query, ctx, params=(batter, batter)).iloc[0]

    bowl_query = "SELECT COALESCE(SUM(RUNS_OFF_BAT), 0) as RUNS_CONCEDED, COUNT(BALL) as BALLS_BOWLED, COALESCE(SUM(CASE WHEN PLAYER_DISMISSED IS NOT NULL AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as WICKETS_TAKEN FROM RAW_DELIVERIES WHERE BOWLER = %s"
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
            wickets_down = st.slider("Wickets Lost", 0, 9, 3)
            overs_completed = st.slider("Overs Completed", 0.0, 19.5, 15.0, 0.1)
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

            total_balls_bowled = int(overs_completed) * 6 + int((overs_completed - int(overs_completed)) * 10)
            balls_remaining = max(120 - total_balls_bowled, 0)
            crr = (current_score / total_balls_bowled) * 6 if total_balls_bowled > 0 else 0.0
            rrr = ((target_to_chase - current_score) / balls_remaining) * 6 if target_to_chase > 0 and balls_remaining > 0 else 0.0

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
            st.bar_chart(df_analysis.set_index("Active Opposing Bowler")[[f"{batter_1} Wicket Danger %", f"{batter_1} Boundary Leak %"]])