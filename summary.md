# Get data
* read csv file
* combine datasets 
* filter for br league
* pick complete data (as shown in excel in 'datacompleteness' col)

# Feature Engineering
* sort by data and reset index 0...N

## Metrics (to be improved)
* Player mastery - career WR on x champ; 
  * __.groupby__ playername and champion
  * get result
  * __.transform__ to keep data same length
  * "__lambda x:__" since calc. is complex and x to represent the results
  * shift to ensure games played BEFORE the day in later scenario where we get add data with live API,  
  * __.expanding__ - create a 'window' with movind ending point since we're gettin more data later
  * __.mean__ to calculate the average (winrate) of the results got in 'result' col
  * __fill empty data__ with 50% wr
* Player streak - WR streak last 5 games
  * .groupby __playername__
  * get __result__
  * apply __transform, lambdax, shift and mean same as above__ since we're getting WR
  * use __.rolling__ instead of .expanding since we want a __determined window__ (5 games)
  * fill NA values with 0.5
* Meta - global champ wr last 50 games in league
  * .groupby __champion__
  * get __result__
  * apply __transform, lambdax, shift, rolling and mean__ with window of 50 to get last 50 games  
  * fill NA values with 0.5
* Team Strength - average of sum of player WR
  * .groupby __playername__
  * get result 
  * get WR same way as above
  * assign WR to the team by grouping __gameid and teamnme__, target all the players WR and apply __.mean__ to get the team average

# Create the pipeline - central nervous system
* convert date col to an object - so python can understand
* reorder rows by date and gameid with .__sort_values__ - prevent gettin a game the player hasn't played yet (data leakage)
* add metrics in dataframe 

# Reshaping data - reshape the vertical list of player data and turn into horizontal row to represent one entire match so the model can compare the stats

* __filter players only__ - exclude the team cols
* __create label for champions__ like "blue_bot_champion" to differ the 10 champions in the match
* __pivot/rotate__ the table 
* __flatten__ columns - ML cannot read multi-level headers
* create "Team Strength" - __.pivot_table()__ to do math and pivot it
* set __aggfunc__ to mean to get average of 5 players WR 
* merge targets, filter on gameid to get result

---

# TO DO
## website
- adjust "entenda os dados" tab, the data is from 2 years, not the entire career
- blue/red on the east west side
- blue/red team ICON display above draft
- dont let repeat champions/team on draft
- players name
- adjust to new split (whether a new team or player is inserted)

## AI/ML model
- more metrics ?
- optimize Meta metrics
- otimize training model 
- adjust to new split/teams/players
- get data from RIOTs live API as split starts