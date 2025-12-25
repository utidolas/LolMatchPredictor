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
    df = df.sort_values(by=['date', 'gameid'])

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

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['date', 'gameid']).reset_index(drop=True)

    df = add_player_metrics(df)
    df = add_meta_metrics(df)
    df = add_team_metrics(df)

    print("Feature Engineering Completed.")
    return df

# ======= Reshaping Data =======
def reshape_to_match_row(df):

    # filter players only
    players_df = df[df['position'] != 'team'].copy()
    players_df['role_side'] = players_df['side'] + "_" + players_df['position']

    # new metrics
    features_to_pivot = [
        'champion', 
        'player_champ_wr',    # Mastery
        'player_recent_form', # Form
        'champ_meta_wr'       # Meta Strength
    ]
    
    # pivot player stats
    match_pivot = players_df.pivot(
        index='gameid', 
        columns='role_side', 
        values=features_to_pivot
    )
    # flatten columns
    match_pivot.columns = [f"{col[1]}_{col[0]}" for col in match_pivot.columns]
    
    # add team stats (since 'team_avg_player_wr' is the same for all 5 players, we take the mean)
    # we grab Blue Team's agg strength and Red Team's agg strength
    team_stats = players_df.pivot_table(index='gameid', columns='side', values='team_avg_player_wr', aggfunc='mean')
    team_stats = team_stats.groupby('gameid').mean() # Collapses the 5 rows into 1
    team_stats.columns = ['Blue_Team_Strength', 'Red_Team_Strength']

    # Merge Targets
    team_rows = df[df['position'] == 'team']
    blue_target = team_rows[team_rows['side'] == 'Blue'][['gameid', 'result']]
    
    final = match_pivot.merge(team_stats, on='gameid').merge(blue_target, on='gameid')
    final.rename(columns={'result': 'blue_win_label'}, inplace=True)
    
    return final

# update main bloc
if __name__ == "__main__":

    raw = get_data() 
    

    enriched = feature_engineering_pipeline(raw)
    final_data = reshape_to_match_row(enriched)
    
    print(final_data.head())
    final_data.to_csv("cblol_training_dataV2.csv", index=False)