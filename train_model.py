import pandas as pd
import joblib
import numpy as np
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report

# get data
df = pd.read_csv("cblol_v3_training.csv")

# champion encoding
champ_cols = [col for col in df.columns if 'champion' in col]
all_champs = pd.concat([df[col].astype(str) for col in champ_cols]).unique()
all_champs = np.append(all_champs, 'Unknown') # Safety net

encoder = LabelEncoder()
encoder.fit(all_champs)

for col in champ_cols:
    df[col] = df[col].astype(str).apply(lambda x: x if x in encoder.classes_ else 'Unknown')
    df[col] = encoder.transform(df[col])

joblib.dump(encoder, "champion_label_encoder.pkl")

# add gaps between teams
roles = ['top', 'jng', 'mid', 'bot', 'sup']
for r in roles:
    # keep original columns
    df[f'{r}_mastery_gap'] = df[f'Blue_{r}_player_champ_wr'] - df[f'Red_{r}_player_champ_wr']
    df[f'{r}_form_gap'] = df[f'Blue_{r}_player_recent_form'] - df[f'Red_{r}_player_recent_form']

df['team_strength_gap'] = df['Blue_Team_Strength'] - df['Red_Team_Strength']

# drop ONLY metadata, keep Raw stats AND Gaps.
# XGBoost handles redundancy well, so giving it both helps it find "High Skill" vs "Low Skill" matches.
metadata_cols = ['gameid', 'date', 'Blue_Team', 'Red_Team', 'blue_win_label', 'patch', 'patch_blue', 'patch_red', 'teamname_red', 'teamname_blue', 'result']

# drop metadata, keep everything else numeric
X = df.drop(columns=[c for c in metadata_cols if c in df.columns])
X = X.select_dtypes(include=[np.number]) # Safety filter
y = df['blue_win_label']

# split data (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# test 50 of hyperparameter to find best model
param_dist = {
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [2, 3, 4, 5],        # Shallow trees often work better for small data
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'subsample': [0.7, 0.8, 1.0],     # Prevent overfitting
    'colsample_bytree': [0.6, 0.8, 1.0]
}

xgb = XGBClassifier(random_state=42, eval_metric='logloss')

# search for best model
search = RandomizedSearchCV(
    estimator=xgb,
    param_distributions=param_dist,
    n_iter=50,                # Try 50 different combos
    scoring='accuracy',
    cv=StratifiedKFold(3),    # Cross-validate to ensure stability
    verbose=1,
    random_state=42,
    n_jobs=-1
)

print("Seraching for hyperparameter")
search.fit(X_train, y_train)

best_model = search.best_estimator_
print(f"\n Best Settings Found: {search.best_params_}")

# finale evaluation
preds = best_model.predict(X_test)
acc = accuracy_score(y_test, preds)

print(f"\nModel Accuracy: {acc:.2%}")
print(classification_report(y_test, preds))

# save the BEST model
# best_model.save_model("cblol_predictor.json")