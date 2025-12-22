'''
load processed data, encode names so the machine can understand them, train the "brain" of the app
'''

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

# load processed data
df = pd.read_csv("cblol_training_data.csv")

# ======= ENCONDING ======= 

# champion names encoding
champ_cols = [col for col in df.columns if 'champion' in col]

# SINGLE encoder for all champions (e.g. whether Morgana is played in any position, it gets the same encoding like ID #23)
global_encoder = LabelEncoder()

# take all unique champions from all 10 columns to fit the encoder
all_champs = pd.concat([df[col] for col in champ_cols]).unique()
global_encoder.fit(all_champs)

# apply encodinf to dataframe
for col in champ_cols:

    # handle unseen champions by mapping them to 'Unknown'
    df[col] = df[col].apply(lambda x: x if x in global_encoder.classes_ else 'Unknown')
    if 'Unknown' not in global_encoder.classes_:
        pass

    df[col] = global_encoder.transform(df[col])

# save the encoder for later use in app.py
joblib.dump(global_encoder, "champion_label_encoder.pkl")
print("Champion Label Encoder saved.")

# ======= MODEL TRAINING =======

# defining feaatures (x) and target (y) && dropping metadata columns not needed
features_to_drop = ['gameid', 'date', 'Blue_Team', 'Red_Team', 'blue_win_label', 'patch', 'patch_blue', 'patch_red', 'teamname_red', 'teamname_blue']

# select only numeric features and encoded champion columns
valid_features = [col for col in df.columns if col not in features_to_drop]

X = df[valid_features]
y = df['blue_win_label']

# train-test split: 80-20
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

# init the brain (XGBoost)
model = XGBClassifier(
    n_estimators=200,      # Number of "trees" in the forest
    learning_rate=0.05,    # How fast it learns (lower is more careful)
    max_depth=4,           # How complex each tree is
    random_state=42
)

print(f"Training on {len(X_train)} matches...")
model.fit(X_train, y_train)

# ======= EVALUATION =======

# predctions
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"\n🏆 Model Accuracy: {accuracy:.2%}")
print("\nDetailed Report:")
print(classification_report(y_test, predictions))

# save the trained brain
model.save_model("cblol_predictor.json")
print("💾 Model saved to cblol_predictor.json")