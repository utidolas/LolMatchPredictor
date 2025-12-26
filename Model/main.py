import pandas as pd
import numpy as np
import joblib
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from xgboost import XGBClassifier
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. Load Assets ---
print("⏳ Loading Model and Data...")
try:
    # Load the trained model
    model = XGBClassifier()
    model.load_model("cblol_predictor.json")
    
    # Load the encoder
    encoder = joblib.load("champion_label_encoder.pkl")
    
    # Load the feature list to ensure correct column order
    with open("model_features.json", "r") as f:
        FEATURE_COLUMNS = json.load(f)

    # Load historical data for stat lookup
    df_history = pd.read_csv("cblol_training_dataV2.csv")
    print("✅ System Ready.")
except Exception as e:
    print(f"❌ Error loading assets: {e}")
    df_history = pd.DataFrame() 
    FEATURE_COLUMNS = []

# --- 2. Define 2025 Rosters (LTA South) ---
ROSTERS = {
    "LOUD": {
        "top": "Robo", "jng": "Croc", "mid": "tinowns", "bot": "Route", "sup": "RedBert"
    },
    "paiN Gaming": {
        "top": "Wizer", "jng": "CarioK", "mid": "dyNquedo", "bot": "TitaN", "sup": "Kuri"
    },
    "FURIA": {
        "top": "Guigo", "jng": "Tatu", "mid": "Tutsz", "bot": "Ayu", "sup": "Jojo"
    },
    "RED Canids": {
        "top": "fNb", "jng": "Aegis", "mid": "Grevthar", "bot": "Brance", "sup": "Frosty"
    },
    "Vivo Keyd Stars": {
        "top": "Guigo", "jng": "Disamis", "mid": "Toucouille", "bot": "SMILEY", "sup": "ProDelta"
    },
    "Fluxo": {
        "top": "Kiari", "jng": "Shini", "mid": "Fuuu", "bot": "Trigo", "sup": "Scuro"
    },
    "Leviatán": {
        "top": "Zothve", "jng": "Pancake", "mid": "TopLop", "bot": "VirusFx", "sup": "IgnaV1"
    },
    "Isurus": {
        "top": "Pan", "jng": "Kaze", "mid": "Seiya", "bot": "Gavotto", "sup": "Jelly"
    }
}

# --- 3. Helper Functions ---

def get_avg_stats(role_prefix, champion, player_name):
    """
    Looks up stats in the historical CSV. 
    """
    col_meta = f"{role_prefix}_champ_meta_wr"
    
    # Default values
    mastery = 0.5
    form = 0.5
    meta = 0.5

    # Check if we have data for this champion in our history
    if not df_history.empty and champion in encoder.classes_:
        # Safe float conversion for Pandas/Numpy values
        try:
            meta_val = df_history[col_meta].mean()
            # Check if meta_val is NaN (not a number)
            if not np.isnan(meta_val):
                meta = float(meta_val)
        except:
            meta = 0.5
        
        # Add random noise for demo simulation
        mastery = float(meta + np.random.uniform(-0.05, 0.05))
        form = float(0.5 + np.random.uniform(-0.1, 0.1))

    return mastery, form, meta

# --- 4. API Endpoints ---

class DraftRequest(BaseModel):
    blue_team: str
    red_team: str
    blue_champs: list[str] # [Top, Jng, Mid, Bot, Sup]
    red_champs: list[str]

@app.post("/predict")
def predict_match(data: DraftRequest):
    if len(data.blue_champs) != 5 or len(data.red_champs) != 5:
        raise HTTPException(status_code=400, detail="Each team must have exactly 5 champions.")

    # 1. Build the Input Vector (Row)
    input_row = {}
    roles = ['top', 'jng', 'mid', 'bot', 'sup']
    
    # Process Blue Team
    blue_stats_display = []
    for i, role in enumerate(roles):
        champ = data.blue_champs[i]
        player = ROSTERS.get(data.blue_team, {}).get(role, "Unknown")
        
        # Encode Champion (handled as int, which is fine)
        champ_enc = int(encoder.transform([champ])[0]) if champ in encoder.classes_ else -1
        input_row[f"Blue_{role}_champion"] = champ_enc
        
        # Get Stats
        m, f, meta = get_avg_stats(f"Blue_{role}", champ, player)
        
        input_row[f"Blue_{role}_player_champ_wr"] = m
        input_row[f"Blue_{role}_player_recent_form"] = f
        input_row[f"Blue_{role}_champ_meta_wr"] = meta
        
        blue_stats_display.append({
            "role": role.upper(),
            "player": player,
            "mastery": f"{m:.0%}",
            "form": f"{f:.0%}"
        })

    # Process Red Team
    red_stats_display = []
    for i, role in enumerate(roles):
        champ = data.red_champs[i]
        player = ROSTERS.get(data.red_team, {}).get(role, "Unknown")
        
        # Encode Champion
        champ_enc = int(encoder.transform([champ])[0]) if champ in encoder.classes_ else -1
        input_row[f"Red_{role}_champion"] = champ_enc
        
        # Get Stats
        m, f, meta = get_avg_stats(f"Red_{role}", champ, player)
        
        input_row[f"Red_{role}_player_champ_wr"] = m
        input_row[f"Red_{role}_player_recent_form"] = f
        input_row[f"Red_{role}_champ_meta_wr"] = meta
        
        red_stats_display.append({
            "role": role.upper(),
            "player": player,
            "mastery": f"{m:.0%}",
            "form": f"{f:.0%}"
        })

    # 2. Add Team Strength (Static for Demo)
    input_row['Blue_Team_Strength'] = 0.55 if data.blue_team in ["LOUD", "paiN Gaming"] else 0.45
    input_row['Red_Team_Strength'] = 0.55 if data.red_team in ["LOUD", "paiN Gaming"] else 0.45
    input_row['team_strength_gap'] = float(input_row['Blue_Team_Strength'] - input_row['Red_Team_Strength'])

    # 3. Calculate Gaps
    for role in roles:
        input_row[f"{role}_mastery_gap"] = float(input_row[f"Blue_{role}_player_champ_wr"] - input_row[f"Red_{role}_player_champ_wr"])
        input_row[f"{role}_form_gap"] = float(input_row[f"Blue_{role}_player_recent_form"] - input_row[f"Red_{role}_player_recent_form"])

    # 4. Create DataFrame
    df_input = pd.DataFrame([input_row])
    
    # Ensure all columns exist
    for col in FEATURE_COLUMNS:
        if col not in df_input.columns:
            df_input[col] = 0.0
            
    df_input = df_input[FEATURE_COLUMNS]

    # predict // XGBoost returns numpy array, MUST convert to python float
    raw_prob = model.predict_proba(df_input)[0][1]
    win_prob = float(raw_prob) 
    
    return {
        "blue_win_percent": round(win_prob * 100, 1),
        "blue_stats": blue_stats_display,
        "red_stats": red_stats_display
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)