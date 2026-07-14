import os
import sqlite3
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import pickle

def train_complex_model():
    """
    Step 3: Multi-Class Predictive Modeling
    Ingests pressure and context variables to predict the probability 
    distribution across boundary, wicket, or dot-ball outcomes simultaneously.
    """
    print("🔮 Step 3: Launching Multi-Class Machine Learning Prediction Pipeline...")
    
    DB_PATH = os.path.join("data", "2_processed", "cricket_analytics.db")
    MODEL_DIR = os.path.join("data", "2_processed")
    
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT striker, bowler, batter_cumulative_runs, batter_balls_faced, 
               balls_remaining, current_wickets_lost, current_run_rate, 
               required_run_rate, event_impact_class 
        FROM analytical_matchup_features
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Clean up null values that occur on the literal first ball of a match
    df.fillna(0, inplace=True)
    
    print("🔤 Scaling LabelEncoders for categorical matrices...")
    le_striker = LabelEncoder()
    le_bowler = LabelEncoder()
    
    df['striker_encoded'] = le_striker.fit_transform(df['striker'])
    df['bowler_encoded'] = le_bowler.fit_transform(df['bowler'])
    
    # Select our massive new contextual feature vectors
    X = df[['striker_encoded', 'bowler_encoded', 'batter_cumulative_runs', 
            'batter_balls_faced', 'balls_remaining', 'current_wickets_lost', 
            'current_run_rate', 'required_run_rate']]
    y = df['event_impact_class']
    
    print("🌲 Fitting Multi-Class Random Forest Model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X, y)
    
    print("📊 Calculating outcome probability distribution matrices...")
    # predict_proba now returns an array of shape (n_samples, 3 classes)
    probs = model.predict_proba(X)
    
    df['prob_dot_single'] = probs[:, 0]
    df['prob_boundary'] = probs[:, 1]
    df['prob_wicket'] = probs[:, 2]
    
    print("💾 Pushing complex predictive data states to SQL warehouse...")
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('gold_matchup_predictions', conn, if_exists='replace', index=False)
    conn.close()
    
    # Save the objects
    with open(os.path.join(MODEL_DIR, "matchup_model.pkl"), "wb") as m_file:
        pickle.dump(model, m_file)
    with open(os.path.join(MODEL_DIR, "encoders.pkl"), "wb") as e_file:
        pickle.dump({'striker': le_striker, 'bowler': le_bowler}, e_file)
        
    print("🎉 Step 3 Complete: High-complexity ML architecture deployed successfully!")

if __name__ == "__main__":
    train_complex_model()