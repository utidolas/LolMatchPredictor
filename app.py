import pandas as pd

# Local path of Oracles Elixirs data
DATA_URL_2024 = "data/2024_LoL_esports_match_data_from_OraclesElixir.csv"
DATA_URL_2025 = "data/2025_LoL_esports_match_data_from_OraclesElixir.csv"


def get_data():
    # load dataset
    df_2024 = pd.read_csv(DATA_URL_2024)
    df_2025 = pd.read_csv(DATA_URL_2025)

    # combine datasets
    full_df = pd.concat([df_2024, df_2025], ignore_index=True)

    # filtering to focus on CBLoL/CBLol ACademy/LTA south matches
    leagues = ['CBLOL', 'LTA S', 'CBLOLA']
    filtered_df = full_df[full_df['league'].isin(leagues)].copy()

    # pick only the complete data
    filtered_df = filtered_df[filtered_df['datacompleteness'] == 'complete']

    return filtered_df

# ======= Metric Calculations =======
def add_player_metrics(df):

    # sort chronologically
    df = df.sort_values(by=['DATE', 'gameid'])

    # mastery - Career WR on specific champion up to that match
    df['player_champ_wr'] = ( df.groupby(['playername', 'champion'])['result'].transform(lambda x: x.shift().expanding().mean())).fillna(0.5)

    # recent form - Career WR on last 5 matches up to that match
    df['player_recent_form'] = (df.groupby('playername')['result'].transform(lambda x: x.shift().rolling(window=5, min_periods=1).mean())).fillna(0.5)
    
    return df

def add_meta_metrics(df):

    # global champion winrate (last 50 games in league)
    df['champ_meta_wr'] = (df.groupby('champion')['result'].transform(lambda x: x.shift().rolling(window=50, min_periods=5).mean())).fillna(0.5)

    # add frequency of pick to weigh against rare champions

    return df

def add_team_metrics(df):
    '''
    Calculate team strength based on the sum of players WR
    Team Strength = Average of (Top WR + Jungle WR + Mid WR + ADC WR + Support WR)
    '''

    # general WR for every player
    df['player_general_wr'] = (df.groupby('playername')['result'].transform(lambda x: x.shift().expanding().mean())).fillna(0.5)

    # assign WR to the Team of the match
    df['team_avg_player_wr'] = (df.groupby(['gameid', 'teamname'])['player_general_wr'].transform('mean'))

    return df

# ======= Pipeline =======
def feature_engineering_pipeline(df):
    return df
# ======= Reshaping Data =======
def reshape_to_match_row(df):

    # keep only player rows
    players_df = df[df['position'] != 'team'].copy()

    # unique keys for columns (Blue_top, Red_jungle, etc)
    players_df['role_side'] = players_df['side'] + "_" + players_df['position']

    # select the features to feed AI
    features_to_pivot = ['champion', 'player_champ_wr', 'player_recent_form']

    # turn rows into columns
    match_pivot = players_df.pivot(
        index='gameid', 
        columns='role_side', 
        values=features_to_pivot
    )

    # ---- Flatten the MultiIndex columns (e.g., ('champion', 'Blue_top') -> 'Blue_top_champion')
    match_pivot.columns = [f"{col[1]}_{col[0]}" for col in match_pivot.columns]
    
    # Re-attach the Target (Did Blue win?) and Match Metadata
    # We grab this from the 'team' rows in the original DF
    team_rows = df[df['position'] == 'team']
    blue_side_results = team_rows[team_rows['side'] == 'Blue'][['gameid', 'result', 'patch', 'teamname']]
    red_side_teams = team_rows[team_rows['side'] == 'Red'][['gameid', 'teamname']]
    
    # Merge everything together
    final_dataset = match_pivot.merge(blue_side_results, on='gameid')
    final_dataset = final_dataset.merge(red_side_teams, on='gameid', suffixes=('_blue', '_red'))
    
    # Rename target for clarity
    final_dataset.rename(columns={'result': 'blue_win_label'}, inplace=True)
    
    return final_dataset

# Update your main block
if __name__ == "__main__":
    raw_data = get_data()
    print(f"1. Raw Data Loaded: {len(raw_data)} rows")
    
    # Step 3b: Feature Engineering
    enriched_data = feature_engineering(raw_data)
    print("2. Features Engineered (Mastery & Form calculated)")
    
    # Step 3c: Reshape
    final_dataset = reshape_to_match_row(enriched_data)
    print(f"3. Reshaped to {len(final_dataset)} unique matches")
    
    # Preview the "Brain" of your AI
    print(final_dataset[['Blue_top_champion', 'Blue_top_player_champ_wr', 'blue_win_label']].head())
    
    # Optional: Save to check manually
    # final_dataset.to_csv("cblol_training_data.csv", index=False)