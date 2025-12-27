import pandas as pd
import numpy as np
import joblib
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from xgboost import XGBClassifier
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- load assets ---
print("Loading Model and Data...")
try:
    model = XGBClassifier()
    model.load_model("cblol_predictor.json")
    encoder = joblib.load("champion_label_encoder.pkl")
    with open("model_features.json", "r") as f:
        FEATURE_COLUMNS = json.load(f)
    df_history = pd.read_csv("cblol_training_dataV2.csv")
    print("System Ready.")
except Exception as e:
    print(f"Error loading assets: {e}")
    df_history = pd.DataFrame() 
    FEATURE_COLUMNS = []

# --- 2025 roster -UPDATE THIS WHEN NEEDED ---
ROSTERS = {
    "LOUD": {"top": "Robo", "jng": "Croc", "mid": "tinowns", "bot": "Route", "sup": "RedBert"},
    "paiN Gaming": {"top": "Wizer", "jng": "CarioK", "mid": "dyNquedo", "bot": "TitaN", "sup": "Kuri"},
    "FURIA": {"top": "Guigo", "jng": "Tatu", "mid": "Tutsz", "bot": "Ayu", "sup": "Jojo"},
    "RED Canids": {"top": "fNb", "jng": "Aegis", "mid": "Grevthar", "bot": "Brance", "sup": "Frosty"},
    "Vivo Keyd Stars": {"top": "Guigo", "jng": "Disamis", "mid": "Toucouille", "bot": "SMILEY", "sup": "ProDelta"},
    "Fluxo": {"top": "Kiari", "jng": "Shini", "mid": "Fuuu", "bot": "Trigo", "sup": "Scuro"},
    "Leviatán": {"top": "Zothve", "jng": "Pancake", "mid": "TopLop", "bot": "VirusFx", "sup": "IgnaV1"},
    "Isurus": {"top": "Pan", "jng": "Kaze", "mid": "Seiya", "bot": "Gavotto", "sup": "Jelly"}
}

# --- helper functions ---
def get_avg_stats(role_prefix, champion, player_name):
    col_meta = f"{role_prefix}_champ_meta_wr"
    mastery = 0.5
    form = 0.5
    meta = 0.5

    if not df_history.empty and champion in encoder.classes_:
        try:
            meta_val = df_history[col_meta].mean()
            if not np.isnan(meta_val):
                meta = float(meta_val)
        except:
            meta = 0.5
        
        mastery = float(meta + np.random.uniform(-0.05, 0.05))
        form = float(0.5 + np.random.uniform(-0.15, 0.15))

    # generate a streak based on form (Simulated for Demo)
    # if form is high, positive streak. If low, negative.
    if form > 0.55:
        streak = int(np.random.randint(2, 6)) # Win streak 2 to 5
    elif form < 0.45:
        streak = int(np.random.randint(-5, -1)) # Loss streak -2 to -5
    else:
        streak = int(np.random.choice([-1, 1])) # 1W or 1L

    return mastery, form, meta, streak

class DraftRequest(BaseModel):
    blue_team: str
    red_team: str
    blue_champs: list[str]
    red_champs: list[str]

@app.post("/predict")
def predict_match(data: DraftRequest):
    if len(data.blue_champs) != 5 or len(data.red_champs) != 5:
        raise HTTPException(status_code=400, detail="Cada time precisa ter exatamente 5 campeões.")

    input_row = {}
    roles = ['top', 'jng', 'mid', 'bot', 'sup']
    
    # process blue side
    blue_stats_display = []
    for i, role in enumerate(roles):
        champ = data.blue_champs[i]
        player = ROSTERS.get(data.blue_team, {}).get(role, "Unknown")
        champ_enc = int(encoder.transform([champ])[0]) if champ in encoder.classes_ else -1
        
        input_row[f"Blue_{role}_champion"] = champ_enc
        m, f, meta, streak = get_avg_stats(f"Blue_{role}", champ, player)
        
        input_row[f"Blue_{role}_player_champ_wr"] = m
        input_row[f"Blue_{role}_player_recent_form"] = f
        input_row[f"Blue_{role}_champ_meta_wr"] = meta
        
        blue_stats_display.append({
            "role": role.upper(),
            "player": player,
            "mastery": f"{m:.0%}",
            "streak": streak # sent to frontedn
        })

    # process red side
    red_stats_display = []
    for i, role in enumerate(roles):
        champ = data.red_champs[i]
        player = ROSTERS.get(data.red_team, {}).get(role, "Unknown")
        champ_enc = int(encoder.transform([champ])[0]) if champ in encoder.classes_ else -1
        
        input_row[f"Red_{role}_champion"] = champ_enc
        m, f, meta, streak = get_avg_stats(f"Red_{role}", champ, player)
        
        input_row[f"Red_{role}_player_champ_wr"] = m
        input_row[f"Red_{role}_player_recent_form"] = f
        input_row[f"Red_{role}_champ_meta_wr"] = meta
        
        red_stats_display.append({
            "role": role.upper(),
            "player": player,
            "mastery": f"{m:.0%}",
            "streak": streak
        })

    # team strength and gaps
    input_row['Blue_Team_Strength'] = 0.55 if data.blue_team in ["LOUD", "paiN Gaming"] else 0.45
    input_row['Red_Team_Strength'] = 0.55 if data.red_team in ["LOUD", "paiN Gaming"] else 0.45
    input_row['team_strength_gap'] = float(input_row['Blue_Team_Strength'] - input_row['Red_Team_Strength'])

    gap_data = []
    for i, role in enumerate(roles):
        m_gap = float(input_row[f"Blue_{role}_player_champ_wr"] - input_row[f"Red_{role}_player_champ_wr"])
        f_gap = float(input_row[f"Blue_{role}_player_recent_form"] - input_row[f"Red_{role}_player_recent_form"])
        
        input_row[f"{role}_mastery_gap"] = m_gap
        input_row[f"{role}_form_gap"] = f_gap
        
        # set up comparison data
        gap_data.append({
            "role": role.upper(),
            "mastery_edge": "Blue" if m_gap > 0 else "Red",
            "mastery_val": abs(round(m_gap * 100, 1)),
            "form_edge": "Blue" if f_gap > 0 else "Red",
            "form_val": abs(round(f_gap * 100, 1))
        })

    # prediction
    df_input = pd.DataFrame([input_row])
    for col in FEATURE_COLUMNS:
        if col not in df_input.columns:
            df_input[col] = 0.0
    df_input = df_input[FEATURE_COLUMNS]
    raw_prob = model.predict_proba(df_input)[0][1]
    blue_win_prob = float(raw_prob) 
    red_win_prob = 1.0 - blue_win_prob

    
    return {
        "blue_win_percent": round(blue_win_prob * 100, 1),
        "red_win_percent": round(red_win_prob * 100, 1), 
        "blue_stats": blue_stats_display,
        "red_stats": red_stats_display,
        "comparison": gap_data
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)