import pandas as pd
import joblib
import json
import numpy as np
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, log_loss

# load data
print(" loading data... ")
df = pd.read_csv("cblol_training_dataV2.csv")

# champion encoding
champ_cols = [col for col in df.columns if 'champion' in col]
all_champs = pd.concat([df[col].astype(str) for col in champ_cols]).unique()
all_champs = np.append(all_champs, 'Unknown') 

encoder = LabelEncoder()
encoder.fit(all_champs)

for col in champ_cols:
    df[col] = df[col].astype(str).apply(lambda x: x if x in encoder.classes_ else 'Unknown')
    df[col] = encoder.transform(df[col])

joblib.dump(encoder, "champion_label_encoder.pkl")

# ======== Feature Engineering ========
# closing the gaps between teams 
roles = ['top', 'jng', 'mid', 'bot', 'sup']
for r in roles:
    df[f'{r}_mastery_gap'] = df[f'Blue_{r}_player_champ_wr'] - df[f'Red_{r}_player_champ_wr']
    df[f'{r}_form_gap'] = df[f'Blue_{r}_player_recent_form'] - df[f'Red_{r}_player_recent_form']

df['team_strength_gap'] = df['Blue_Team_Strength'] - df['Red_Team_Strength']

# drop metadata
metadata_cols = ['gameid', 'date', 'Blue_Team', 'Red_Team', 'blue_win_label', 
                 'patch', 'patch_blue', 'patch_red', 'teamname_red', 'teamname_blue', 'result']
X = df.drop(columns=[c for c in metadata_cols if c in df.columns])
X = X.select_dtypes(include=[np.number]) # Keep only numbers

# saving list of features for later use on the website
# The website MUST use this exact order later.
feature_list = list(X.columns)
with open("model_features.json", "w") as f:
    json.dump(feature_list, f)
print(f" feature list saved: ({len(feature_list)} features) to model_features.json")

y = df['blue_win_label']

# split and train data 80/20
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)

# model training (test different parameters)
model = XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=3,       # shallow to prevent overfitting
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

print("🧠 Training model...")
model.fit(X_train, y_train)

# evaluation
preds = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1] # probability of Blue Win

acc = accuracy_score(y_test, preds)
loss = log_loss(y_test, probs)

print(f"\nACCURACY: {acc:.2%}")
print(f"Log Loss (Confidence Error): {loss:.4f} (Lower is better)")
print("\n" + classification_report(y_test, preds))

# save the brain
model.save_model("cblol_predictor.json")
print("Model saved successfully.")