import pymongo
import pandas as pd
import csv

client = pymongo.MongoClient("mongodb+srv://abhinavr2121:MangoMongo404500!@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
db = client.RacquetStats
collection = db.Stats

data = pd.DataFrame(list(collection.find()))
distinct_winners = pd.DataFrame(list(collection.distinct('Winner')))
distinct_losers = pd.DataFrame(list(collection.distinct('Loser')))

distinct_locations = pd.DataFrame(list(collection.distinct('Location')))
distinct_players = pd.concat([distinct_winners, distinct_losers])
names = pd.DataFrame(distinct_players[0].unique())

names.to_excel('data/countries.xlsx')