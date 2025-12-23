# Get data
* read csv file
* combine datasets 
* filter for br league
* pick complete data (as shown in excel in 'datacompleteness' col)

# Feature Engineering
* sort by data and reset index 0...N

## Metrics (to be improved)
* Player mastery & player streak - career WR on x champ; 
  * .groupby playername and champion
  * get result
  * .transform to keep data same length
  * "lambda x:" since calc. is complex and x to represent the results
  * shift to ensure games played BEFORE the day in later scenario where we get add data with live API,  
  * .expanding - create a 'window' with movind ending point since we're gettin more data later
  * .mean to calculate the average (winrate) of the results got in 'result' col
* Meta (champion strength)
* Team Strength

# TO DO
## website
- blue/red on the east west side
- blue/red team name display above draft
- interactive carousel
- carousel scroll
- api to get lol data for website
- dont let repeat champions on draft
- api to call our model
- bootstrap
- search bar carousel
- players name
- adjust to new split (whether a new team or player is inserted)
## AI/ML model
- more metrics ?
- otimize training model 
- adjust to new split/teams/players
- get data from RIOTs live API as split starts