import os
import snowflake.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def run_snowflake_feature_engineering():
    print("🚀 Re-engineering Cloud Feature Layer with Target Labels...")
    
    try:
        ctx = snowflake.connector.connect(
            user=os.getenv("SF_USER"),
            password=os.getenv("SF_PASSWORD"),
            account=os.getenv("SF_ACCOUNT"),
            warehouse=os.getenv("SF_WAREHOUSE"),
            database=os.getenv("SF_DATABASE"),
            schema=os.getenv("SF_SCHEMA")
        )
        cursor = ctx.cursor()
        print("✅ Connected to Snowflake Virtual compute clusters.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    feature_generation_sql = """
    CREATE OR REPLACE TABLE ANALYTICAL_MATCHUP_FEATURES AS
    WITH match_innings_base AS (
        SELECT 
            MATCH_ID, INNINGS, BALL, STRIKER, BOWLER, RUNS_OFF_BAT, EXTRAS,
            (RUNS_OFF_BAT + EXTRAS) as TOTAL_BALL_RUNS,
            CASE WHEN WICKET_TYPE IS NOT NULL AND WICKET_TYPE NOT IN ('run out', 'retired hurt') THEN 1 ELSE 0 END as IS_WICKET,
            120 - (FLOOR(BALL) * 6 + (BALL - FLOOR(BALL)) * 10) as BALLS_REMAINING
        FROM RAW_DELIVERIES
        WHERE INNINGS IN (1, 2)
    ),
    match_outcomes AS (
        SELECT 
            MATCH_ID,
            SUM(CASE WHEN INNINGS = 1 THEN TOTAL_BALL_RUNS ELSE 0 END) as T1_TOTAL,
            SUM(CASE WHEN INNINGS = 2 THEN TOTAL_BALL_RUNS ELSE 0 END) as T2_TOTAL
        FROM match_innings_base
        GROUP BY MATCH_ID
    ),
    running_metrics AS (
        SELECT 
            b.MATCH_ID, b.INNINGS, b.BALL, b.STRIKER, b.BOWLER, b.RUNS_OFF_BAT, b.IS_WICKET, b.BALLS_REMAINING,
            SUM(b.TOTAL_BALL_RUNS) OVER (PARTITION BY b.MATCH_ID, b.INNINGS ORDER BY b.BALL ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as CURRENT_TEAM_SCORE,
            SUM(b.IS_WICKET) OVER (PARTITION BY b.MATCH_ID, b.INNINGS ORDER BY b.BALL ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) as CURRENT_WICKETS_LOST,
            o.T1_TOTAL as INNINGS_1_TARGET
        FROM match_innings_base b
        JOIN match_outcomes o ON b.MATCH_ID = o.MATCH_ID
    )
    SELECT 
        r.MATCH_ID, r.INNINGS, r.BALL, r.STRIKER, r.BOWLER, r.BALLS_REMAINING,
        COALESCE(r.CURRENT_WICKETS_LOST, 0) as CURRENT_WICKETS_LOST,
        
        CASE 
            WHEN (120 - r.BALLS_REMAINING) > 0 THEN (COALESCE(r.CURRENT_TEAM_SCORE, 0) / (120 - r.BALLS_REMAINING)) * 6 
            ELSE 0.0 
        END as CURRENT_RUN_RATE,
        
        -- Calculate structural targets and RUNS_NEEDED explicitly
        CASE 
            WHEN r.INNINGS = 2 THEN COALESCE(r.INNINGS_1_TARGET + 1, 0)
            ELSE 0 
        END as TARGET_SCORE,
        
        CASE 
            WHEN r.INNINGS = 2 THEN GREATEST(COALESCE(r.INNINGS_1_TARGET + 1, 0) - COALESCE(r.CURRENT_TEAM_SCORE, 0), 0)
            ELSE 0 
        END as RUNS_NEEDED,
        
        CASE 
            WHEN r.INNINGS = 2 AND r.BALLS_REMAINING > 0 THEN (GREATEST(COALESCE(r.INNINGS_1_TARGET + 1, 0) - COALESCE(r.CURRENT_TEAM_SCORE, 0), 0) / r.BALLS_REMAINING) * 6
            ELSE 0.0 
        END as REQUIRED_RUN_RATE,
        
        -- Materialize ultimate CHASE_WON label cleanly (1 = Batting team won, 0 = Lost)
        CASE 
            WHEN r.INNINGS = 2 AND o.T2_TOTAL >= o.T1_TOTAL THEN 1
            ELSE 0
        END as CHASE_WON
    FROM running_metrics r
    JOIN match_outcomes o ON r.MATCH_ID = o.MATCH_ID
    WHERE r.INNINGS = 2; -- We only store second innings chasing scenarios for optimal feature memory footprint
    """

    print("⚡ Materializing structural feature targets down to Snowflake storage layers...")
    try:
        cursor.execute(feature_generation_sql)
        cursor.execute("SELECT COUNT(*) FROM ANALYTICAL_MATCHUP_FEATURES;")
        print(f"🎉 Success! Ingested {cursor.fetchone()[0]:,} labeled vectors into ANALYTICAL_MATCHUP_FEATURES.")
    except Exception as e:
        print(f"❌ Feature processing failed: {e}")
    finally:
        cursor.close()
        ctx.close()

if __name__ == "__main__":
    run_snowflake_feature_engineering()