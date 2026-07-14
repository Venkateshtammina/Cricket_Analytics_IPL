import os
import snowflake.connector
import pandas as pd
import streamlit as st
import pickle
import numpy as np
from dotenv import load_dotenv

# Load local environment parameters if present
load_dotenv()

# Set premium dashboard layout configuration
st.set_page_config(
    page_title="Elite IPL Strategy Engine",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI styling framework injection
st.markdown("""
<style>
    .reportview-container { background: #0f1116; color: #ffffff; }
    .metric-card {
        background-color: #1a1e26;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-card-alert {
        background-color: #1a1e26;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #e74c3c;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-card-success {
        background-color: #1a1e26;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2ecc71;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    h1, h2, h3 { color: #f3f4f6 !important; font-family: 'Helvetica Neue', sans-serif; }
    p { color: #9ca3af; }
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

def get_team_rosters(limit_recent_players=True):
    ctx = get_snowflake_connection()
    if limit_recent_players:
        recent_matches_query = "SELECT DISTINCT MATCH_ID FROM RAW_DELIVERIES ORDER BY MATCH_ID DESC LIMIT 20"
        recent_matches = pd.read_sql(recent_matches_query, ctx)['MATCH_ID'].tolist()
        match_id_string = ','.join(map(str, recent_matches))
        
        batting_query = f"SELECT DISTINCT BATTING_TEAM as TEAM, STRIKER as PLAYER FROM RAW_DELIVERIES WHERE MATCH_ID IN ({match_id_string})"
        bowling_query = f"SELECT DISTINCT BOWLING_TEAM as TEAM, BOWLER as PLAYER FROM RAW_DELIVERIES WHERE MATCH_ID IN ({match_id_string})"
    else:
        batting_query = "SELECT DISTINCT BATTING_TEAM as TEAM, STRIKER as PLAYER FROM RAW_DELIVERIES"
        bowling_query = "SELECT DISTINCT BOWLING_TEAM as TEAM, BOWLER as PLAYER FROM RAW_DELIVERIES"
        
    df_batters = pd.read_sql(batting_query, ctx)
    df_batters['ROLE'] = 'batter'
    df_bowlers = pd.read_sql(bowling_query, ctx)
    df_bowlers['ROLE'] = 'bowler'
    
    df_rosters = pd.concat([df_batters, df_bowlers], ignore_index=True)
    ctx.close()
    return df_rosters

def get_detailed_stats(batter, bowler):
    ctx = get_snowflake_connection()
    h2h_query = """
        SELECT 
            COALESCE(SUM(RUNS_OFF_BAT), 0) as TOTAL_RUNS, 
            COUNT(BALL) as TOTAL_BALLS,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 4 THEN 1 ELSE 0 END), 0) as TOTAL_FOURS,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 6 THEN 1 ELSE 0 END), 0) as TOTAL_SIXES,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 1 THEN 1 ELSE 0 END), 0) as TOTAL_ONES,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 2 THEN 1 ELSE 0 END), 0) as TOTAL_TWOS,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 3 THEN 1 ELSE 0 END), 0) as TOTAL_THREES,
            COALESCE(SUM(CASE WHEN RUNS_OFF_BAT = 0 THEN 1 ELSE 0 END), 0) as TOTAL_DOTS,
            COALESCE(SUM(CASE WHEN PLAYER_DISMISSED IS NOT NULL AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as TOTAL_WICKETS
        FROM RAW_DELIVERIES WHERE STRIKER = %s AND BOWLER = %s
    """
    df_h2h = pd.read_sql(h2h_query, ctx, params=(batter, bowler)).iloc[0]
    
    bat_query = """
        SELECT 
            COALESCE(SUM(RUNS_OFF_BAT), 0) as RUNS, 
            COUNT(BALL) as BALLS,
            COUNT(DISTINCT MATCH_ID) as TOTAL_INNINGS,
            COALESCE(SUM(CASE WHEN PLAYER_DISMISSED = %s AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as TOTAL_DISMISSALS
        FROM RAW_DELIVERIES WHERE STRIKER = %s
    """
    df_bat = pd.read_sql(bat_query, ctx, params=(batter, batter)).iloc[0]
    
    bowl_query = """
        SELECT 
            COALESCE(SUM(RUNS_OFF_BAT), 0) as RUNS_CONCEDED, 
            COUNT(BALL) as BALLS_BOWLED,
            COALESCE(SUM(CASE WHEN PLAYER_DISMISSED IS NOT NULL AND WICKET_TYPE IS NOT NULL THEN 1 ELSE 0 END), 0) as WICKETS_TAKEN
        FROM RAW_DELIVERIES WHERE BOWLER = %s
    """
    df_bowl = pd.read_sql(bowl_query, ctx, params=(bowler,)).iloc[0]
    ctx.close()
    return df_h2h, df_bat, df_bowl

def calculate_historical_win_percentage(balls_left, wickets_lost, current_score, target_score):
    runs_needed = target_score - current_score
    if runs_needed <= 0: return 100.0
    if balls_left <= 0: return 0.0
    if wickets_lost >= 10: return 0.0
    
    req_run_rate = (runs_needed / balls_left) * 6
    ctx = get_snowflake_connection()
    
    # 1. Broadly pull down matching historical chasing windows
    query = """
        SELECT BALLS_REMAINING, RUNS_NEEDED, CURRENT_WICKETS_LOST, REQUIRED_RUN_RATE, CHASE_WON
        FROM ANALYTICAL_MATCHUP_FEATURES
        WHERE BALLS_REMAINING BETWEEN %s AND %s
    """
    df_features = pd.read_sql(query, ctx, params=(max(balls_left - 12, 0), balls_left + 12))
    ctx.close()
    
    if df_features.empty:
        wickets_left = 10 - wickets_lost
        base_prob = 50.0 + (wickets_left * 4.5) - (req_run_rate * 4.0) + (balls_left * 0.1)
        return max(min(base_prob, 95.0), 5.0)

    # 2. FEATURE SCALING Normalization for KNN Accuracy
    # Normalize features to a common 0-1 scale so runs/balls don't overpower the single-digit wicket vector
    b_remain_max = df_features['BALLS_REMAINING'].max() or 1
    runs_need_max = df_features['RUNS_NEEDED'].max() or 1
    rrr_max = df_features['REQUIRED_RUN_RATE'].max() or 1
    
    # Standardize historical vectors
    h_b = df_features['BALLS_REMAINING'] / b_remain_max
    h_r = df_features['RUNS_NEEDED'] / runs_need_max
    h_w = df_features['CURRENT_WICKETS_LOST'] / 10.0
    h_rrr = df_features['REQUIRED_RUN_RATE'] / rrr_max
    
    # Standardize active live inputs
    s_b = balls_left / b_remain_max
    s_r = runs_needed / runs_need_max
    s_w = wickets_lost / 10.0
    s_rrr = req_run_rate / rrr_max

    # Compute Euclidean distance on normalized scales with balanced weights
    df_features['dist'] = np.sqrt(
        ((h_b - s_b) * 1.0) ** 2 +
        ((h_r - s_r) * 1.5) ** 2 +
        ((h_w - s_w) * 3.5) ** 2 + # Wickets now carry significant scaling priority
        ((h_rrr - s_rrr) * 2.0) ** 2
    )
    
    # Select closest matching historical data blocks
    k_neighbors = df_features.nsmallest(120, 'dist')
    raw_historical_pct = k_neighbors['CHASE_WON'].mean() * 100
    
    # 3. DIRECT CRICKETING STATE PENALTY
    # Mathematically enforce that fewer wickets left ALWAYS equals lower win probability
    wickets_left = 10 - wickets_lost
    # Exponential resource curve penalizes tail-end setups heavily
    resource_multiplier = (wickets_left / 10.0) ** 0.45
    
    # Blend the raw history with the absolute wicket resource limit state
    calibrated_pct = raw_historical_pct * resource_multiplier
    
    # Final pressure calibration adjustments based on required run rate lines
    if req_run_rate > 10.0:
        calibrated_pct -= (wickets_lost * 1.5)
        
    return max(min(calibrated_pct, 98.0), 2.0)

# --- APP LAYOUT RUNNER ---
model, encoders = load_ml_objects()
df_rosters = get_team_rosters(limit_recent_players=True)

if model is None or df_rosters.empty:
    st.error("❌ Critical cloud assets missing. Ensure your models are committed.")
else:
    all_batters_global = sorted(df_rosters[df_rosters['ROLE'] == 'batter']['PLAYER'].unique())
    all_bowlers_global = sorted(df_rosters[df_rosters['ROLE'] == 'bowler']['PLAYER'].unique())
    all_teams = sorted(df_rosters['TEAM'].unique())
    
    st.title("⚡ IPL Front-Office Match Optimization Room")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📊 Room 1: Live Simulation Deck", "🛡️ Room 2: Franchise Matrix Board"])
    
    with tab1:
        c_setup1, c_setup2 = st.columns([1, 2])
        with c_setup1:
            st.markdown("### 🎛️ Situation Configuration")
            sim_batter = st.selectbox("Active Batter", all_batters_global, index=0)
            sim_bowler = st.selectbox("Active Bowler", all_bowlers_global, index=0)
            current_score = st.number_input("Current Runs", min_value=0, value=120)
            wickets_down = st.slider("Wickets Down", 0, 9, 3)
            overs_completed = st.slider("Overs Completed", 0.0, 19.5, 15.0, 0.1)
            target_to_chase = st.number_input("Target to Chase", min_value=0, value=160)
            
        with c_setup2:
            st.markdown("### 📈 Live Performance Analytics Dashboard")
            h2h, bat_p, bowl_p = get_detailed_stats(sim_batter, sim_bowler)
            
            if h2h['TOTAL_BALLS'] > 0:
                sr = (h2h['TOTAL_RUNS'] / h2h['TOTAL_BALLS']) * 100
                h2h_wickets = int(h2h['TOTAL_WICKETS'])
                
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1: st.markdown(f"<div class='metric-card'><h5>Matchup Runs</h5><h2>{int(h2h['TOTAL_RUNS'])}</h2></div>", unsafe_allow_html=True)
                with kpi2: st.markdown(f"<div class='metric-card'><h5>Balls Faced</h5><h2>{int(h2h['TOTAL_BALLS'])}</h2></div>", unsafe_allow_html=True)
                with kpi3: st.markdown(f"<div class='metric-card-success'><h5>Strike Rate</h5><h2>{sr:.1f}</h2></div>", unsafe_allow_html=True)
                with kpi4: st.markdown(f"<div class='metric-card-alert'><h5>Wickets Lost</h5><h2>{h2h_wickets}</h2></div>", unsafe_allow_html=True)
            else:
                st.info("💡 Displaying general career metrics below.")
                kpi1, kpi2 = st.columns(2)
                with kpi1:
                    b_sr = (bat_p['RUNS'] / bat_p['BALLS']) * 100 if bat_p['BALLS'] > 0 else 0
                    dismissals = int(bat_p['TOTAL_DISMISSALS'])
                    b_avg = bat_p['RUNS'] / dismissals if dismissals > 0 else bat_p['RUNS'] / max(int(bat_p['TOTAL_INNINGS']), 1)
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <h5>{sim_batter} Career Stats</h5>
                        <h2>{int(bat_p['RUNS'])} Runs</h2>
                        <p style='margin:0; font-size:14px;'><b>Avg:</b> {b_avg:.2f} | <b>SR:</b> {b_sr:.1f} | <b>Innings:</b> {int(bat_p['TOTAL_INNINGS'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with kpi2:
                    bw_econ = (bowl_p['RUNS_CONCEDED'] / bowl_p['BALLS_BOWLED']) * 6 if bowl_p['BALLS_BOWLED'] > 0 else 0
                    bw_wickets = int(bowl_p['WICKETS_TAKEN'])
                    bw_avg = bowl_p['RUNS_CONCEDED'] / bw_wickets if bw_wickets > 0 else np.nan
                    bw_sr = bowl_p['BALLS_BOWLED'] / bw_wickets if bw_wickets > 0 else np.nan
                    
                    avg_str = f"{bw_avg:.2f}" if not np.isnan(bw_avg) else "N/A"
                    sr_str = f"{bw_sr:.1f}" if not np.isnan(bw_sr) else "N/A"
                    
                    st.markdown(f"""
                    <div class='metric-card-alert'>
                        <h5>{sim_bowler} Career Stats</h5>
                        <h2>{bw_wickets} Wickets</h2>
                        <p style='margin:0; font-size:14px;'><b>Econ:</b> {bw_econ:.2f} | <b>Avg:</b> {avg_str} | <b>SR:</b> {sr_str}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            total_balls_bowled = int(overs_completed) * 6 + int((overs_completed - int(overs_completed)) * 10)
            balls_remaining = max(120 - total_balls_bowled, 0)
            crr = (current_score / total_balls_bowled) * 6 if total_balls_bowled > 0 else 0.0
            rrr = ((target_to_chase - current_score) / balls_remaining) * 6 if target_to_chase > 0 and balls_remaining > 0 else 0.0
            
            st.markdown("### 🏁 Live Chase Win Predictor Vector")
            win_pct = calculate_historical_win_percentage(balls_remaining, wickets_down, current_score, target_to_chase)
            w_c1, w_c2 = st.columns(2)
            with w_c1: st.metric("Batting Team Win Chance", f"{win_pct:.1f}%")
            with w_c2: st.metric("Bowling Team Win Chance", f"{(100.0 - win_pct):.1f}%")
            st.progress(win_pct / 100.0)
            
            try:
                bat_enc = encoders['striker'].transform([sim_batter])[0]
                bow_enc = encoders['bowler'].transform([sim_bowler])[0]
                v = np.array([[bat_enc, bow_enc, 25, 15, balls_remaining, wickets_down, crr, rrr]])
                ml_p = model.predict_proba(v)[0]
                
                st.markdown("### 🔮 Tactical Micro-Event Forecasting Vector")
                pm1, pm2, pm3 = st.columns(3)
                with pm1: st.markdown(f"<div class='metric-card'><h5>Rotation Prob</h5>   <h3>{ml_p[0]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm2: st.markdown(f"<div class='metric-card-success'><h5>Boundary Prob</h5><h3>{ml_p[1]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm3: st.markdown(f"<div class='metric-card-alert'><h5>Dismissals Risk</h5><h3>{ml_p[2]*100:.1f}%</h3></div>", unsafe_allow_html=True)
            except ValueError:
                pass

    with tab2:
        st.header("Opposing Team Optimization Matrix Room")
        st.markdown("---")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1: my_team = st.selectbox("Your Analytics Franchise Context", all_teams, index=0)
        with t_col2: opposing_team = st.selectbox("Opposing Franchise", [t for t in all_teams if t != my_team], index=0)
            
        available_batters = sorted(df_rosters[(df_rosters['TEAM'] == my_team) & (df_rosters['ROLE'] == 'batter')]['PLAYER'].unique())
        available_bowlers = sorted(df_rosters[(df_rosters['TEAM'] == opposing_team) & (df_rosters['ROLE'] == 'bowler')]['PLAYER'].unique())
        
        p_col1, p_col2 = st.columns(2)
        with p_col1: batter_1 = st.selectbox("Active Striker (Recent Only)", available_batters, index=0)
        with p_col2: batter_2 = st.selectbox("Active Non-Striker (Recent Only)", [b for b in available_batters if b != batter_1], index=min(1, len(available_batters)-1))
            
        st.markdown("---")
        analysis_records = []
        for bowler in available_bowlers:
            try:
                h2h_1, _, bowl_prof = get_detailed_stats(batter_1, bowler)
                h2h_2, _, _ = get_detailed_stats(batter_2, bowler)
                
                b_enc = encoders['bowler'].transform([bowler])[0]
                b1_enc = encoders['striker'].transform([batter_1])[0]
                v1 = np.array([[b1_enc, b_enc, 20, 15, 30, 3, 7.5, 9.0]])
                p1 = model.predict_proba(v1)[0]
                
                b2_enc = encoders['striker'].transform([batter_2])[0]
                v2 = np.array([[b2_enc, b_enc, 15, 12, 30, 3, 7.5, 9.0]])
                p2 = model.predict_proba(v2)[0]
                
                b_wickets = int(bowl_prof['WICKETS_TAKEN'])
                c_avg = round(bowl_prof['RUNS_CONCEDED'] / b_wickets, 2) if b_wickets > 0 else np.nan
                c_sr = round(bowl_prof['BALLS_BOWLED'] / b_wickets, 1) if b_wickets > 0 else np.nan
                
                analysis_records.append({
                    "Active Opposing Bowler": bowler,
                    f"{batter_1} Wicket Danger %": round(p1[2] * 100, 1),
                    f"{batter_1} Boundary Leak %": round(p1[1] * 100, 1),
                    f"{batter_2} Wicket Danger %": round(p2[2] * 100, 1),
                    f"{batter_2} Boundary Leak %": round(p2[1] * 100, 1),
                    "Career Bowling Avg": c_avg,
                    "Career Bowling SR": c_sr,
                    "Combined Career Wickets": int(h2h_1['TOTAL_WICKETS'] + h2h_2['TOTAL_WICKETS']),
                    "Combined Career Runs Given": int(h2h_1['TOTAL_RUNS'] + h2h_2['TOTAL_RUNS'])
                })
            except ValueError:
                continue
                
        if analysis_records:
            df_analysis = pd.DataFrame(analysis_records).sort_values(by=f"{batter_1} Wicket Danger %", ascending=False).reset_index(drop=True)
            st.dataframe(df_analysis, use_container_width=True)
            
            st.markdown("### 📈 Visual Matchup Threat Spectrum Mapping (Full Partnership View)")
            chart_columns = [f"{batter_1} Wicket Danger %", f"{batter_1} Boundary Leak %", f"{batter_2} Wicket Danger %", f"{batter_2} Boundary Leak %"]
            chart_df = df_analysis.set_index("Active Opposing Bowler")[chart_columns]
            st.bar_chart(chart_df)