# 🏏 IPL Strategy Engine

An advanced, real-time IPL analytics dashboard that combines **historical cricket data**, **machine learning**, and **interactive visualizations** to provide ball-by-ball insights, live chase win probabilities, and batter-bowler matchup intelligence.

Built using **Python**, **Streamlit**, **Snowflake**, and **Scikit-Learn**, the application enables analysts, cricket enthusiasts, and franchises to explore match situations through a modern interactive interface.

---

## 🚀 Features

### 📊 Live Match Simulation

Configure any IPL chase scenario by adjusting:

- Current Score
- Target Score
- Overs Completed
- Wickets Down
- Active Batter
- Active Bowler

The dashboard updates all analytics in real time.

---

### 📈 Live Chase Win Predictor

Predicts the batting team's winning probability using historical IPL data.

The prediction considers:

- Balls Remaining
- Runs Needed
- Wickets Lost
- Historical chase situations
- Required Run Rate
- Current Run Rate

---

### 🎯 Batter vs Bowler Analytics

Displays historical head-to-head statistics including:

- Runs scored
- Balls faced
- Strike Rate
- Fours & Sixes
- Dot Balls
- Dismissals

---

### 👤 Player Career Statistics

Automatically displays career metrics for both players.

#### Batter

- Total Runs
- Batting Average
- Strike Rate
- Innings Played

#### Bowler

- Wickets
- Economy
- Bowling Average
- Strike Rate

---

### 🤖 Next Ball Prediction

A trained Scikit-Learn model predicts the probability of the next delivery resulting in:

- Rotation (0–3 Runs)
- Boundary
- Wicket

Predictions are generated instantly using encoded player information and live match features.

---

### 🛡️ Franchise Matchup Matrix

Compare every available bowler against two selected batters from another franchise.

The dashboard ranks bowlers based on:

- Wicket Threat
- Boundary Leakage
- Historical Matchups
- Career Bowling Statistics

---

## 🏗️ Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | Streamlit |
| Programming Language | Python |
| Data Warehouse | Snowflake |
| Machine Learning | Scikit-Learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Pickle |
| Environment Management | python-dotenv |

---

# 📂 Project Structure

```text
Cricket_Analytics_IPL/
│
├── app.py
├── requirements.txt
├── README.md
├── .env
│
├── data/
│   └── 2_processed/
│       ├── matchup_model.pkl
│       └── encoders.pkl
│
└── .streamlit/
    └── secrets.toml
```

---

# ⚙️ Installation

Clone the repository.

```bash
git clone https://github.com/Venkateshtammina/Cricket_Analytics_IPL.git

cd Cricket_Analytics_IPL
```

Install dependencies.

```bash
pip install -r requirements.txt
```

---

# 🔐 Configuration

Create a `.env` file.

```env
SF_USER=your_username
SF_PASSWORD=your_password
SF_ACCOUNT=your_account
SF_WAREHOUSE=your_warehouse
SF_DATABASE=your_database
SF_SCHEMA=your_schema
```

For Streamlit Cloud deployment, place the same credentials inside:

```text
.streamlit/secrets.toml
```

---

# ▶️ Running the Application

```bash
streamlit run app.py
```

The dashboard will be available at

```
http://localhost:8501
```

---

# 🗄️ Data Sources

The project uses two primary Snowflake tables.

## RAW_DELIVERIES

Contains every IPL delivery.

Used for:

- Player statistics
- Head-to-head records
- Match totals
- Historical analysis

---

## ANALYTICAL_MATCHUP_FEATURES

Contains engineered features for every delivery.

Important columns include:

- MATCH_ID
- INNINGS
- BALL
- STRIKER
- BOWLER
- CURRENT_TEAM_SCORE
- CURRENT_WICKETS_LOST
- BALLS_REMAINING
- CURRENT_RUN_RATE
- TARGET_SCORE
- REQUIRED_RUN_RATE
- MATCHUP_OUTCOME

---

# 🤖 Machine Learning Model

The application uses a pre-trained multi-class classifier.

### Input Features

- Encoded Batter
- Encoded Bowler
- Historical Matchup Runs
- Historical Balls Faced
- Balls Remaining
- Wickets Lost
- Current Run Rate
- Required Run Rate

### Output Classes

- Rotation Probability
- Boundary Probability
- Wicket Probability

---

# 📊 Win Probability Model

The chase predictor estimates the batting team's winning chances by comparing the current match situation against historical IPL data.

The model evaluates:

- Balls Remaining
- Runs Needed
- Wickets Lost
- Current Run Rate
- Required Run Rate

to identify similar historical chase situations and estimate the probability of a successful chase.

---

# 📸 Dashboard Preview

The application includes:

- Live Match Simulation
- Historical Head-to-Head Statistics
- Career Player Profiles
- Chase Win Predictor
- Next Ball Prediction
- Franchise Matchup Matrix

---

# 📦 Dependencies

Main libraries used:

```text
streamlit
snowflake-connector-python
pandas
numpy
scikit-learn
python-dotenv
pickle
```

---

# 📈 Future Improvements

- K-Nearest Neighbor based historical win prediction
- Ball-by-ball win probability graph
- Venue-based analytics
- Batter form index
- Bowler spell analysis
- Partnership prediction
- Match momentum tracking
- Wagon Wheel visualization
- Pitch and venue adjustment
- Win Probability Timeline

---

# 🤝 Contributing

Contributions are welcome.

If you'd like to improve the project:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a Pull Request.

---

# 📄 License

This project is intended for educational and analytical purposes.

---

# 👨‍💻 Author

**Venkatesh Tammina**

Live:https://venkateshtammina-cricket-analytics-ipl-app-iiyn1q.streamlit.app/

---

## ⭐ If you found this project useful, consider giving it a star on GitHub!
