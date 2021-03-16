from flask import Flask, render_template, request
import pymongo
import pandas as pd
import json
import numpy as np

app = Flask(__name__)

client = pymongo.MongoClient("mongodb+srv://abhinavr2121:MangoMongo404500!@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
db = client.RacquetStats
collection = db.Stats

@app.route('/')
def main_root():
	distinct_winners = pd.DataFrame(list(collection.distinct('Winner')))
	distinct_losers = pd.DataFrame(list(collection.distinct('Loser')))

	distinct_locations = pd.DataFrame(list(collection.distinct('Location')))
	distinct_players = pd.concat([distinct_winners, distinct_losers])

	names = distinct_players[0].unique().tolist()
	locations = distinct_locations[0].unique().tolist()
	return render_template('index.html', 
							names = names, 
							surface = ['Hard', 'Clay', 'Grass', 'Carpet'],
							locations = locations)

@app.route('/results', methods = ['POST', 'GET'])
def get_results():
	if request.method == 'POST':
		route = 0
		p1 = request.form.get('p1').capitalize()
		p2 = request.form.get('p2').capitalize()
		surface = request.form.get('surface').capitalize()
		location = request.form.get('location').capitalize()
		query = None
		if len(p1) > 0 and len(p2) > 0:
			query = {'$and': [{'Winner': {'$regex': p1 + '|' + p2, '$options': 'i'}},
							  {'Loser': {'$regex': p1 + '|' + p2, '$options': 'i'}},
							  {'Surface': {'$regex': surface,'$options': 'i'}},
							  {'Location': {'$regex': location, '$options': 'i'}}]}
			route = 1
		elif len(p1) > 0 and len(p2) == 0 and len(surface) == 0:
			query = {'$and': [{'$or': [{'Winner': {'$regex': '.*' + p1 + '.*', '$options': 'i'}},
							 {'Loser': {'$regex': '.*' + p1 + '.*', '$options': 'i' }}]},
							 {'Surface': {'$regex': surface}},
							 {'Location': {'$regex': location, '$options': 'i'}}]}
			route = 2
		elif len(p1) == 0 and len(p2) == 0 and len(surface) == 0 and len(location) > 0:
			query = {'$and': [{'Location': {'$regex': location, '$options': 'i'}}]}
			route = 3
		elif len(p1) == 0 and len(p2) == 0 and len(surface) > 0:
			query = {'$and': [{'Surface': {'$regex': surface}}]}
			route = 4

		results = pd.DataFrame(list(collection.find(query)))
		results['Date'] = pd.to_datetime(results['Date'], format = '%m/%d/%Y')
		results = results.sort_values('Date', ascending = False)
		results['Date'] = results['Date'].dt.strftime('%m/%d/%Y')

		if route == 1:
			return render_template('results1.html', 
									data = results, 
									name1 = p1, 
									name2 = p2, 
									np = np,
									p1 = results[results['Winner'].str.upper().str.contains(p1.upper())],
									p2 = results[results['Winner'].str.upper().str.contains(p2.upper())])
		elif route == 2:
			return render_template('results2.html', 
									data = results,
									name1 = p1,
									np = np,
									pd = pd,
									p1_win = results[results['Winner'].str.upper().str.contains(p1.upper())],
									p1_loss = results[results['Loser'].str.upper().str.contains(p1.upper())])
		elif route == 3:
			return render_template('results3.html', 
									data = results,
									location = location,
									np = np,
									pd = pd,
									location_sub = results[results['Location'].str.upper().str.contains(location.upper())])
		elif route == 4:
			return render_template('results4.html',
									data = results,
									surface = surface,
									np = np,
									pd = pd,
									surface_sub = results[results['Surface'].str.upper().str.contains(surface.upper())])
	else:
		return 'gotted'