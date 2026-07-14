import os
import sqlite3
import pandas as pd
import streamlit as st
import pickle
import numpy as np

# Set premium dashboard configurations
st.set_page_config(
    page_title="Elite IPL Strategy Engine",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom corporate styling framework injection
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
DB_PATH = os.path.join("data", "2_processed", "cricket_analytics.db")

@st.cache_resource
def load_ml_objects():
    """Loads the system's trained model and encoders into execution memory"""
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        with open(MODEL_PATH, "rb") as m_f:
            model = pickle.load(m_f)
        with open(ENCODER_PATH, "rb") as e_f:
            encoders = pickle.load(e_f)
        return model, encoders
    return None, None

def get_team_rosters(limit_recent_players=True):
    """
    Maps players to their historical teams.
    Filters out BOTH batters and bowlers who haven't played 
    in the most recent 20 matches of our database.
    """
    conn = sqlite3.connect(DB_PATH)
    if limit_recent_players:
        recent_matches_query = "SELECT DISTINCT match_id FROM raw_deliveries ORDER BY match_id DESC LIMIT 20"
        recent_matches = pd.read_sql_query(recent_matches_query, conn)['match_id'].tolist()
        match_id_string = ','.join(map(str, recent_matches))
        
        batting_query = f"SELECT DISTINCT batting_team as team, striker as player FROM raw_deliveries WHERE match_id IN ({match_id_string})"
        bowling_query = f"SELECT DISTINCT bowling_team as team, bowler as player FROM raw_deliveries WHERE match_id IN ({match_id_string})"
    else:
        batting_query = "SELECT DISTINCT batting_team as team, striker as player FROM raw_deliveries"
        bowling_query = "SELECT DISTINCT bowling_team as team, bowler as player FROM raw_deliveries"
        
    df_batters = pd.read_sql_query(batting_query, conn)
    df_batters['role'] = 'batter'
    df_bowlers = pd.read_sql_query(bowling_query, conn)
    df_bowlers['role'] = 'bowler'
    
    df_rosters = pd.concat([df_batters, df_bowlers], ignore_index=True)
    conn.close()
    return df_rosters

def get_detailed_stats(batter, bowler):
    """Dynamically fetches head-to-head stats, falling back to overall career profiles if needed"""
    conn = sqlite3.connect(DB_PATH)
    
    # Query 1: Direct Head to Head (Calibrated with COALESCE to prevent NoneType math errors)
    h2h_query = """
        SELECT 
            COALESCE(SUM(runs_off_bat), 0) as total_runs, 
            COUNT(ball) as total_balls,
            COALESCE(SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END), 0) as total_fours,
            COALESCE(SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END), 0) as total_sixes,
            COALESCE(SUM(CASE WHEN runs_off_bat = 1 THEN 1 ELSE 0 END), 0) as total_ones,
            COALESCE(SUM(CASE WHEN runs_off_bat = 2 THEN 1 ELSE 0 END), 0) as total_twos,
            COALESCE(SUM(CASE WHEN runs_off_bat = 3 THEN 1 ELSE 0 END), 0) as total_threes,
            COALESCE(SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END), 0) as total_dots,
            COALESCE(SUM(CASE WHEN player_dismissed IS NOT NULL AND wicket_type IS NOT NULL THEN 1 ELSE 0 END), 0) as total_wickets
        FROM raw_deliveries WHERE striker = ? AND bowler = ?
    """
    df_h2h = pd.read_sql_query(h2h_query, conn, params=(batter, bowler)).iloc[0]
    
    # Query 2: Overall Batter Profile
    bat_query = """
        SELECT 
            COALESCE(SUM(runs_off_bat), 0) as runs, 
            COUNT(ball) as balls,
            COALESCE(SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END), 0) as fours,
            COALESCE(SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END), 0) as sixes,
            COALESCE(SUM(CASE WHEN runs_off_bat = 1 THEN 1 ELSE 0 END), 0) as ones,
            COALESCE(SUM(CASE WHEN runs_off_bat = 2 THEN 1 ELSE 0 END), 0) as twos,
            COALESCE(SUM(CASE WHEN runs_off_bat = 3 THEN 1 ELSE 0 END), 0) as threes,
            COALESCE(SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END), 0) as dots
        FROM raw_deliveries WHERE striker = ?
    """
    df_bat = pd.read_sql_query(bat_query, conn, params=(batter,)).iloc[0]
    
    # Query 3: Overall Bowler Profile
    bowl_query = """
        SELECT 
            COALESCE(SUM(runs_off_bat), 0) as runs_conceded, 
            COUNT(ball) as balls_bowled,
            COALESCE(SUM(CASE WHEN player_dismissed IS NOT NULL AND wicket_type IS NOT NULL THEN 1 ELSE 0 END), 0) as wickets_taken
        FROM raw_deliveries WHERE bowler = ?
    """
    df_bowl = pd.read_sql_query(bowl_query, conn, params=(bowler,)).iloc[0]
    conn.close()
    return df_h2h, df_bat, df_bowl

def calculate_historical_win_percentage(balls_left, wickets_lost, req_run_rate):
    if req_run_rate <= 0:
        return 100.0
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT match_id, is_wicket, runs_off_bat, required_run_rate
        FROM analytical_matchup_features
        WHERE innings = 2 
          AND balls_remaining BETWEEN ? AND ?
          AND current_wickets_lost = ?
          AND required_run_rate BETWEEN ? AND ?
    """
    df_sim = pd.read_sql_query(query, conn, params=(max(balls_left - 6, 0), balls_left + 6, wickets_lost, max(req_run_rate - 1.5, 0.0), req_run_rate + 1.5))
    conn.close()
    
    if df_sim.empty:
        wickets_left = 10 - wickets_lost
        base_prob = 50.0 + (wickets_left * 4.0) - (req_run_rate * 3.5) + (balls_left * 0.15)
        return max(min(base_prob, 99.0), 1.0)
        
    unique_matches = df_sim['match_id'].unique()
    successful_chases = 0
    
    conn = sqlite3.connect(DB_PATH)
    for m_id in unique_matches:
        f_score = pd.read_sql_query(f"SELECT SUM(runs_off_bat + extras) as final_score FROM raw_deliveries WHERE match_id = {m_id} AND innings = 2", conn).iloc[0]['final_score']
        t_score = pd.read_sql_query(f"SELECT SUM(runs_off_bat + extras) as target_score FROM raw_deliveries WHERE match_id = {m_id} AND innings = 1", conn).iloc[0]['target_score']
        if f_score is not None and t_score is not None and f_score > t_score:
            successful_chases += 1
    conn.close()
    return (successful_chases / len(unique_matches)) * 100

# --- APP LAYOUT RUNNER ---
model, encoders = load_ml_objects()
df_rosters = get_team_rosters(limit_recent_players=True)

if model is None or df_rosters.empty:
    st.error("❌ Critical system data assets are missing. Please verify your pipeline paths.")
else:
    all_batters_global = sorted(df_rosters[df_rosters['role'] == 'batter']['player'].unique())
    all_bowlers_global = sorted(df_rosters[df_rosters['role'] == 'bowler']['player'].unique())
    all_teams = sorted(df_rosters['team'].unique())
    
    st.title("⚡ IPL Front-Office Match Optimization Room")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📊 Room 1: Live Simulation Deck", "🛡️ Room 2: Franchise Matrix Board"])
    
    # ==========================================
    # 🏏 ROOM 1: LIVE SIMULATION DECK
    # ==========================================
    with tab1:
        c_setup1, c_setup2 = st.columns([1, 2])
        
        with c_setup1:
            st.markdown("### 🎛️ Situation Configuration")
            sim_batter = st.selectbox("Active Batter", all_batters_global, index=0)
            sim_bowler = st.selectbox("Active Bowler", all_bowlers_global, index=0)
            current_score = st.number_input("Current Runs", min_value=0, value=120)
            wickets_down = st.slider("Wickets Lost", 0, 9, 3)
            overs_completed = st.slider("Overs Completed", 0.0, 19.5, 15.0, 0.1)
            target_to_chase = st.number_input("Target to Chase", min_value=0, value=160)
            
        with c_setup2:
            st.markdown("### 📈 Live Performance Analytics Dashboard")
            h2h, bat_p, bowl_p = get_detailed_stats(sim_batter, sim_bowler)
            
            if h2h['total_balls'] > 0:
                sr = (h2h['total_runs'] / h2h['total_balls']) * 100
                econ = (h2h['total_runs'] / h2h['total_balls']) * 6
                h2h_wickets = int(h2h['total_wickets'])
                
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1: st.markdown(f"<div class='metric-card'><h5>Matchup Runs</h5><h2>{int(h2h['total_runs'])}</h2></div>", unsafe_allow_html=True)
                with kpi2: st.markdown(f"<div class='metric-card'><h5>Balls Faced</h5><h2>{int(h2h['total_balls'])}</h2></div>", unsafe_allow_html=True)
                with kpi3: st.markdown(f"<div class='metric-card-success'><h5>Strike Rate</h5><h2>{sr:.1f}</h2></div>", unsafe_allow_html=True)
                with kpi4: st.markdown(f"<div class='metric-card-alert'><h5>Wickets Lost</h5><h2>{h2h_wickets}</h2></div>", unsafe_allow_html=True)
            else:
                st.info("💡 No direct head-to-head records found. Displaying general career metrics below.")
                kpi1, kpi2 = st.columns(2)
                with kpi1:
                    b_sr = (bat_p['runs'] / bat_p['balls']) * 100 if bat_p['balls'] > 0 else 0
                    st.markdown(f"<div class='metric-card'><h5>{sim_batter} Career Runs</h5><h2>{int(bat_p['runs'])} (SR {b_sr:.1f})</h2></div>", unsafe_allow_html=True)
                with kpi2:
                    bw_econ = (bowl_p['runs_conceded'] / bowl_p['balls_bowled']) * 6 if bowl_p['balls_bowled'] > 0 else 0
                    st.markdown(f"<div class='metric-card-alert'><h5>{sim_bowler} Wickets</h5><h2>{int(bowl_p['wickets_taken'])} (Econ {bw_econ:.2f})</h2></div>", unsafe_allow_html=True)
            
            total_balls_bowled = int(overs_completed) * 6 + int((overs_completed - int(overs_completed)) * 10)
            balls_remaining = max(120 - total_balls_bowled, 0)
            crr = (current_score / total_balls_bowled) * 6 if total_balls_bowled > 0 else 0.0
            rrr = ((target_to_chase - current_score) / balls_remaining) * 6 if target_to_chase > 0 and balls_remaining > 0 else 0.0
            
            st.markdown("### 🏁 Live Chase Win Predictor Vector")
            win_pct = calculate_historical_win_percentage(balls_remaining, wickets_down, rrr)
            
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
                with pm1: st.markdown(f"<div class='metric-card'><h5>Rotation Prob</h5><h3>{ml_p[0]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm2: st.markdown(f"<div class='metric-card-success'><h5>Boundary Prob</h5><h3>{ml_p[1]*100:.1f}%</h3></div>", unsafe_allow_html=True)
                with pm3: st.markdown(f"<div class='metric-card-alert'><h5>Dismissals Risk</h5><h3>{ml_p[2]*100:.1f}%</h3></div>", unsafe_allow_html=True)
            except ValueError:
                pass

    # ==========================================
    # 🛡️ ROOM 2: FRANCHISE MATRIX BOARD
    # ==========================================
    with tab2:
        st.header("Opposing Team Optimization Matrix Room")
        st.markdown("---")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1: my_team = st.selectbox("Your Analytics Franchise Context", all_teams, index=0)
        with t_col2: opposing_team = st.selectbox("Opposing Franchise", [t for t in all_teams if t != my_team], index=0)
            
        available_batters = sorted(df_rosters[(df_rosters['team'] == my_team) & (df_rosters['role'] == 'batter')]['player'].unique())
        available_bowlers = sorted(df_rosters[(df_rosters['team'] == opposing_team) & (df_rosters['role'] == 'bowler')]['player'].unique())
        
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
                
                # Predict metrics for Batter 1
                b1_enc = encoders['striker'].transform([batter_1])[0]
                v1 = np.array([[b1_enc, b_enc, 20, 15, 30, 3, 7.5, 9.0]])
                p1 = model.predict_proba(v1)[0]
                
                # Predict metrics for Batter 2
                b2_enc = encoders['striker'].transform([batter_2])[0]
                v2 = np.array([[b2_enc, b_enc, 15, 12, 30, 3, 7.5, 9.0]])
                p2 = model.predict_proba(v2)[0]
                
                b_wickets = int(bowl_prof['wickets_taken'])
                c_avg = round(bowl_prof['runs_conceded'] / b_wickets, 2) if b_wickets > 0 else np.nan
                c_sr = round(bowl_prof['balls_bowled'] / b_wickets, 1) if b_wickets > 0 else np.nan
                
                # Fully mapped parameters to prevent key alignment skips
                analysis_records.append({
                    "Active Opposing Bowler": bowler,
                    f"{batter_1} Wicket Danger %": round(p1[2] * 100, 1),
                    f"{batter_1} Boundary Leak %": round(p1[1] * 100, 1),
                    f"{batter_2} Wicket Danger %": round(p2[2] * 100, 1),
                    f"{batter_2} Boundary Leak %": round(p2[1] * 100, 1),
                    "Career Bowling Avg": c_avg,
                    "Career Bowling SR": c_sr,
                    "Combined Career Wickets": int(h2h_1['total_wickets'] + h2h_2['total_wickets']),
                    "Combined Career Runs Given": int(h2h_1['total_runs'] + h2h_2['total_runs'])
                })
            except ValueError:
                continue
                
        if analysis_records:
            df_analysis = pd.DataFrame(analysis_records).sort_values(by=f"{batter_1} Wicket Danger %", ascending=False).reset_index(drop=True)
            st.dataframe(df_analysis, use_container_width=True)
            
            # --- FULL PARTNERSHIP SPECTRUM PLOTTING ENGINE ---
            st.markdown("### 📈 Visual Matchup Threat Spectrum Mapping (Full Partnership View)")
            chart_columns = [
                f"{batter_1} Wicket Danger %", 
                f"{batter_1} Boundary Leak %",
                f"{batter_2} Wicket Danger %",
                f"{batter_2} Boundary Leak %"
            ]
            
            chart_df = df_analysis.set_index("Active Opposing Bowler")[chart_columns]
            st.bar_chart(chart_df)
            
            dangerous_bowler = df_analysis.iloc[0]['Active Opposing Bowler']
            st.warning(f"📋 **Analytic Scouting Takeaway**: **{dangerous_bowler}** exhibits the strongest contextual match threat value against **{batter_1}**.")
        else:
            st.info("No unified active player records map across this franchise split layout.")