import os
import pickle
import pandas as pd
import numpy as np
import snowflake.connector
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

def train_matchup_model_from_snowflake():
    print("🚀 Initializing Cloud Data Model Training Pipeline...")
    
    # --- STEP 1: ESTABLISH SECURE OPERATIONAL HANDSHAKE ---
    try:
        ctx = snowflake.connector.connect(
            user=os.getenv("SF_USER"),
            password=os.getenv("SF_PASSWORD"),
            account=os.getenv("SF_ACCOUNT"),
            warehouse=os.getenv("SF_WAREHOUSE"),
            database=os.getenv("SF_DATABASE"),
            schema=os.getenv("SF_SCHEMA")
        )
        print("✅ Secure connection established with Snowflake.")
    except Exception as e:
        print(f"❌ Connection to Snowflake failed: {e}")
        return

    # --- STEP 2: EXTRACT ENGINEERED CLOUD FEATURE MATRIX ---
    print("📥 Downloading materialized features table from the cloud...")
    query = """
        SELECT 
            STRIKER, BOWLER, BALLS_REMAINING, CURRENT_WICKETS_LOST,
            CURRENT_RUN_RATE, REQUIRED_RUN_RATE, MATCHUP_OUTCOME
        FROM ANALYTICAL_MATCHUP_FEATURES
    """
    df = pd.read_sql(query, ctx)
    ctx.close()
    print(f"📦 Successfully ingested {len(df):,} engineered training vectors into memory.")

    # Standardize column naming conventions
    df.columns = df.columns.str.lower()

    # --- STEP 3: ENCODE CATEGORICAL STRINGS ---
    print("🏷️ Initializing dynamic label encoding matrices...")
    encoders = {}
    categorical_cols = ['striker', 'bowler']
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le

    # Split targets and structural features
    X = df[['striker', 'bowler', 'balls_remaining', 'current_wickets_lost', 'current_run_rate', 'required_run_rate']]
    y = df['matchup_outcome']

    # Handle any unexpected infinite or null variations safely
    X = X.replace([np.inf, -np.inf], 0).fillna(0)

    # Stratified split to keep training and testing sets balanced
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- STEP 4: ENSEMBLE MODEL TRAINING ---
    print("🧠 Training Random Forest Classifier across distributed compute layers...")
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=12, 
        random_state=42, 
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("🎯 Model training loop finalized.")

    # --- STEP 5: PERFORMANCE EVALUATION ---
    y_pred = model.predict(X_test)
    print("\n📊 Model Classification Report:")
    print(classification_report(y_pred, y_test, target_names=['Dot/Single (0)', 'Boundary (1)', 'Wicket (2)']))

    # --- STEP 6: SERIALIZE MACHINE LEARNING OBJECTS ---
    processed_dir = os.path.join("data", "2_processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    model_path = os.path.join(processed_dir, "matchup_model.pkl")
    encoder_path = os.path.join(processed_dir, "encoders.pkl")

    print("💾 Serializing model artifacts locally...")
    with open(model_path, "wb") as m_f:
        pickle.load = pickle.dump(model, m_f)
    with open(encoder_path, "wb") as e_f:
        pickle.load = pickle.dump(encoders, e_f)
        
    print(f"🎉 Success! Machine learning model assets saved safely:\n 🔹 {model_path}\n 🔹 {encoder_path}")
    print("🏆 Step 3 Production Model Training Pipeline Complete!")

if __name__ == "__main__":
    train_matchup_model_from_snowflake();