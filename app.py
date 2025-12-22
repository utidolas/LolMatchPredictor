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

def feature_engineering(df):
    
    # sort by date
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['date', 'gameid'])

    # reset index to ensure 0...N index
    df = df.reset_index(drop=True)

    # player mastery calculator (win rate on specific champion e.g. Robo's win rate on Renekton before this match)
    df['player_champ_wr'] = (
        df.groupby(['playername', 'champion'])['result']
        .transform(lambda x: x.shift().expanding().mean())
    )

    # player win rate in last 5 games regardless the champion
    df['player_recent_form'] = (
        df.groupby('playername')['result']
        .transform(lambda x: x.shift().rolling(window=5, min_periods=1).mean())
    )

    # fill NA values to 50% in case first time playing
    df['player_champ_wr'] = df['player_champ_wr'].fillna(0.5)
    df['player_recent_form'] = df['player_recent_form'].fillna(0.5) 

    return df

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