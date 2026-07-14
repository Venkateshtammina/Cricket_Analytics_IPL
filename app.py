import os
import snowflake.connector
import pandas as pd
import streamlit as st
import pickle
import numpy as np
from dotenv import load_dotenv

# Initialize tracking environment parameters
load_dotenv()

# Set premium dashboard layout configuration
st.set_page_config(
    page_title="Elite IPL Strategy Engine",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI styling framework injection (Glassmorphism & Sports Analytics Dark Mode)
st.markdown("""
<style>
    .stApp { background-color: #0d0f13; color: #f3f4f6; }
    div[data-testid="stSidebar"] { background-color: #131722; border-right: 1px solid #1f293d; }
    
    /* Custom metric card designs */
    .metric-card-neutral {
        background-color: #1c2030;
        padding: 22px;
        border-radius: 12px;
        border-left: 5px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }
    .metric-card-success {
        background-color: #1c2030;
        padding: 22px;
        border-radius: 12px;
        border-left: 5px solid #10b981;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }
    .metric-card-alert {
        background-color: #1c2030;
        padding: 22px;
        border-radius: 12px;
        border-left: 5px solid #ef4444;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        margin-bottom: 15px;
    }
    .sub-metric-text {
        margin: 5px 0 0 0; 
        font-size: 13px; 
        color: #9ca3af;
        line-height: 1.4;
    }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c2030;
        color: #9ca3af;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0d0f13 !important; font-weight: bold; }
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

@st.cache_data(ttl=7200) # Cache rosters for 2 hours to accelerate navigation loading
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

@st.cache_data(ttl=7200) # Cache static profiles to completely cut network trip overheads
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

@st.cache_data(ttl=7200) # High-Performance Cache Layer isolates KNN candidate matrix updates
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
    st.error("❌ Critical System Ingestion block missing configuration parameters.")
else:
    all_batters_global = sorted(df_rosters[df_rosters['ROLE'] == 'batter']['PLAYER'].unique())
    all_bowlers_global = sorted(df_rosters[df_rosters['ROLE'] == 'bowler']['PLAYER'].unique())
    all_teams = sorted(df_rosters['TEAM'].unique())
    
    st.title("⚡ IPL STRATEGY ENGINE")
    st.markdown("<p style='color:#6b7280; margin-top:-15px;'>Enterprise Smart Predictive Operations Center</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📊 Live Simulation Deck", "🛡️ Franchise Matrix Board"])
    
    with tab1:
        c_setup1, c_setup2 = st.columns([1, 2], gap="large")
        with c_setup1:
            st.markdown("### 🎛️ Match Parameters")
            sim_batter = st.selectbox("Active Striker", all_batters_global, index=0)
            sim_bowler = st.selectbox("Active Bowler", all_bowlers_global, index=0)
            current_score = st.number_input("Current Runs Scored", min_value=0, value=120)
            wickets_down = st.slider("Wickets Lost", 0, 9, 3)
            overs_completed = st.slider("Overs Completed", 0.0, 19.5, 15.0, 0.1)
            target_to_chase = st.number_input("Target to Chase", min_value=0, value=160)
            
        with c_setup2:
            st.markdown("### 📈 Live In-Game Metrics")
            h2h, bat_p, bowl_p = get_detailed_stats(sim_batter, sim_bowler)
            
            k_prof1, k_prof2 = st.columns(2)
            with k_prof1:
                b_sr = (bat_p['RUNS'] / bat_p['BALLS']) * 100 if bat_p['BALLS'] > 0 else 0
                b_avg = bat_p['RUNS'] / int(bat_p['TOTAL_DISMISSALS']) if int(bat_p['TOTAL_DISMISSALS']) > 0 else bat_p['RUNS'] / max(int(bat_p['TOTAL_INNINGS']), 1)
                st.markdown(f"<div class='metric-card-neutral'><h5>{sim_batter}</h5><h2>{int(bat_p['RUNS'])} Runs</h2><p class='sub-metric-text'><b>Avg:</b> {b_avg:.2f} | <b>SR:</b> {b_sr:.1f} | <b>Inn:</b> {int(bat_p['TOTAL_INNINGS'])}</p></div>", unsafe_allow_html=True)
            with k_prof2:
                bw_econ = (bowl_p['RUNS_CONCEDED'] / bowl_p['BALLS_BOWLED']) * 6 if bowl_p['BALLS_BOWLED'] > 0 else 0
                bw_wickets = int(bowl_p['WICKETS_TAKEN'])
                bw_avg = bowl_p['RUNS_CONCEDED'] / bw_wickets if bw_wickets > 0 else np.nan
                avg_str = f"{bw_avg:.2f}" if not np.isnan(bw_avg) else "N/A"
                st.markdown(f"<div class='metric-card-alert'><h5>{sim_bowler}</h5><h2>{bw_wickets} Wickets</h2><p class='sub-metric-text'><b>Econ:</b> {bw_econ:.2f} | <b>Avg:</b> {avg_str}</p></div>", unsafe_allow_html=True)
            
            total_balls_bowled = int(overs_completed) * 6 + int((overs_completed - int(overs_completed)) * 10)
            balls_remaining = max(120 - total_balls_bowled, 0)
            crr = (current_score / total_balls_bowled) * 6 if total_balls_bowled > 0 else 0.0
            rrr = ((target_to_chase - current_score) / balls_remaining) * 6 if target_to_chase > 0 and balls_remaining > 0 else 0.0
            
            st.markdown("### 🏁 Vector Live Win Probability")
            win_pct = calculate_historical_win_percentage(balls_remaining, wickets_down, current_score, target_to_chase)
            
            w_c1, w_c2 = st.columns(2)
            with w_c1: st.metric("Chasing Team Chance", f"{win_pct:.1f}%")
            with w_c2: st.metric("Defending Team Chance", f"{(100.0 - win_pct):.1f}%")
            st.progress(win_pct / 100.0)
            
            try:
                bat_enc = encoders['striker'].transform([sim_batter])[0]
                bow_enc = encoders['bowler'].transform([sim_bowler])[0]
                v = np.array([[bat_enc, bow_enc, 25, 15, balls_remaining, wickets_down, crr, rrr]])
                ml_p = model.predict_proba(v)[0]
                
                st.markdown("### 🔮 Next-Ball Event Forecast Vectors")
                pm1, pm2, pm3 = st.columns(3)
                with pm1: st.markdown(f"<div class='metric-card-neutral'><h5>Single / Dot</h5><h3>{ml_p[0]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm2: st.markdown(f"<div class='metric-card-success'><h5>Boundary</h5><h3>{ml_p[1]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm3: st.markdown(f"<div class='metric-card-alert'><h5>Dismissal Risk</h5><h3>{ml_p[2]*100:.1f}%</h3></div>", unsafe_allow_html=True)
            except Exception: pass

    with tab2:
        st.header("Opposing Franchise Matchup Matrix Board")
        t_col1, t_col2 = st.columns(2)
        with t_col1: my_team = st.selectbox("Your Analytics Context Franchise", all_teams, index=0)
        with t_col2: opposing_team = st.selectbox("Target Opponent Context", [t for t in all_teams if t != my_team], index=0)
            
        available_batters = sorted(df_rosters[(df_rosters['TEAM'] == my_team) & (df_rosters['ROLE'] == 'batter')]['PLAYER'].unique())
        available_bowlers = sorted(df_rosters[(df_rosters['TEAM'] == opposing_team) & (df_rosters['ROLE'] == 'bowler')]['PLAYER'].unique())
        
        p_col1, p_col2 = st.columns(2)
        with p_col1: batter_1 = st.selectbox("Franchise Batter A", available_batters, index=0)
        with p_col2: batter_2 = st.selectbox("Franchise Batter B", [b for b in available_batters if b != batter_1], index=min(1, len(available_batters)-1))
            
        st.markdown("---")
        analysis_records = []
        for bowler in available_bowlers:
            try:
                h2h_1, _, bowl_prof = get_detailed_stats(batter_1, bowler)
                b_enc = encoders['bowler'].transform([bowler])[0]
                b1_enc = encoders['striker'].transform([batter_1])[0]
                v1 = np.array([[b1_enc, b_enc, 20, 15, 30, 3, 7.5, 9.0]])
                p1 = model.predict_proba(v1)[0]
                
                b2_enc = encoders['striker'].transform([batter_2])[0]
                v2 = np.array([[b2_enc, b_enc, 15, 12, 30, 3, 7.5, 9.0]])
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
            st.dataframe(df_analysis, use_container_width=True)
            st.markdown("### 📈 Visual Matchup Threat Spectrum Mapping")
            st.bar_chart(df_analysis.set_index("Active Opposing Bowler")[[f"{batter_1} Wicket Danger %", f"{batter_1} Boundary Leak %"]])