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