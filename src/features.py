import os
import sqlite3
import pandas as pd

def build_matchup_features():
    """
    Step 2: Advanced Context Transformation Layer
    Computes required run rates, scoring pressure variables, 
    and multi-class target labels across thousands of deliveries.
    """
    print("🧹 Step 2: Starting Advanced SQL Feature Engineering...")
    
    DB_PATH = os.path.join("data", "2_processed", "cricket_analytics.db")
    conn = sqlite3.connect(DB_PATH)
    
    # --- COMPLEX SQL ARCHITECTURE ---
    # We layer multiple CTEs to compute target scores and remaining resource vectors
    advanced_query = """
    WITH base_deliveries AS (
        SELECT 
            match_id,
            innings,
            ball,
            striker,
            bowler,
            runs_off_bat,
            extras,
            (runs_off_bat + extras) as total_delivery_runs,
            CASE WHEN wicket_type IS NOT NULL AND player_dismissed IS NOT NULL THEN 1 ELSE 0 END as is_wicket,
            -- Calculate balls remaining in a standard T20 match (120 balls total)
            120 - ((CAST(ball AS INT) * 6) + ((ball - CAST(ball AS INT)) * 10)) as balls_remaining
        FROM raw_deliveries
    ),
    innings_aggregates AS (
        SELECT 
            *,
            -- Cumulative team score up to this delivery
            SUM(total_delivery_runs) OVER(PARTITION BY match_id, innings ORDER BY ball) as current_team_score,
            -- Cumulative wickets lost up to this delivery
            SUM(is_wicket) OVER(PARTITION BY match_id, innings ORDER BY ball) as current_wickets_lost,
            -- Running total of runs scored by individual batter
            SUM(runs_off_bat) OVER(PARTITION BY match_id, innings, striker ORDER BY ball) as batter_cumulative_runs,
            -- Running count of balls faced by individual batter
            COUNT(runs_off_bat) OVER(PARTITION BY match_id, innings, striker ORDER BY ball) as batter_balls_faced
        FROM base_deliveries
    ),
    first_innings_totals AS (
        SELECT 
            match_id,
            MAX(current_team_score) as target_score
        FROM innings_aggregates
        WHERE innings = 1
        GROUP BY match_id
    )
    SELECT 
        a.match_id,
        a.innings,
        a.ball,
        a.striker,
        a.bowler,
        a.runs_off_bat,
        a.is_wicket,
        a.batter_cumulative_runs,
        a.batter_balls_faced,
        a.balls_remaining,
        a.current_wickets_lost,
        
        -- Current Run Rate (CRR)
        ROUND((CAST(a.current_team_score AS REAL) / (120 - a.balls_remaining)) * 6, 2) as current_run_rate,
        
        -- Required Run Rate (RRR) for 2nd Innings Chases
        CASE 
            WHEN a.innings = 2 AND a.balls_remaining > 0 
            THEN ROUND((CAST((t.target_score + 1 - a.current_team_score) AS REAL) / a.balls_remaining) * 6, 2)
            ELSE 0.0
        END as required_run_rate
        
    FROM innings_aggregates a
    LEFT JOIN first_innings_totals t ON a.match_id = t.match_id
    ORDER BY a.match_id, a.innings, a.ball;
    """
    
    print("⚙️ Executing algorithmic window functions and match state tracking...")
    df_adv = pd.read_sql_query(advanced_query, conn)
    
    # --- DEFINE COMPLEX MULTI-CLASS ML TARGET ---
    # Class 0: Dot or Single (Low immediate event impact)
    # Class 1: Boundary (4 or 6 - Batting success)
    # Class 2: Wicket (Bowling success)
    def assign_impact_class(row):
        if row['is_wicket'] == 1: return 2
        if row['runs_off_bat'] in [4, 6]: return 1
        return 0
        
    df_adv['event_impact_class'] = df_adv.apply(assign_impact_class, axis=1)
    
    print("💾 Committing high-leverage analytical data features back to warehouse...")
    df_adv.to_sql('analytical_matchup_features', conn, if_exists='replace', index=False)
    conn.close()
    print("🎉 Step 2 Complete: Highly complex contextual feature tables locked down!")

if __name__ == "__main__":
    build_matchup_features()