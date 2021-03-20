import pandas as pd
import numpy as np
import pymongo

client = pymongo.MongoClient("mongodb+srv://normal-user:7Pv02lHlo3Dzdxai@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
db = client.RacquetStats
collection = db.Stats

distinct_winners = pd.DataFrame(list(collection.distinct('Winner')))
distinct_losers = pd.DataFrame(list(collection.distinct('Loser')))

distinct_players = pd.concat([distinct_winners, distinct_losers])
distinct_names = distinct_players[0].unique().tolist()

last_updated = '3/7/2021'
new_data = pd.read_excel('data/new_data.xlsx')

# RULES
new_data_winners = np.array(new_data['Winner'].unique())
new_data_losers = np.array(new_data['Loser'].unique())
new_data_players = np.concatenate([new_data_losers, new_data_winners])
new_players = np.setdiff1d(new_data_players, distinct_names)
print(new_players)