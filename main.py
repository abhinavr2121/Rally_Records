from flask import Flask, render_template, request, abort
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
							locations = locations,
							years = str(list(range(2005, 2022))))

@app.route('/results/', methods = ['POST', 'GET'])
@app.route('/results/location/<location>', methods = ['POST', 'GET'])
@app.route('/results/player/<player>/', methods = ['POST', 'GET'])
def get_results(player = None, location = None):
	if request.method == 'POST':
		route = 0
		p1 = request.form.get('p1').capitalize()
		p2 = request.form.get('p2').capitalize()
		surface = request.form.get('surface').capitalize()
		location = request.form.get('location').capitalize()
		years = request.form.get('year')
		query = None
		if len(p1) > 0 and len(p2) > 0: # two players
			query = {'$and': [{'Winner': {'$regex': p1 + '|' + p2, '$options': 'i'}},
							  {'Loser': {'$regex': p1 + '|' + p2, '$options': 'i'}},
							  {'Surface': {'$regex': surface,'$options': 'i'}},
							  {'Location': {'$regex': location, '$options': 'i'}},
							  {'Date': {'$regex': '.*' + years + '.*', '$options': 'i'}}]}
			route = 1
		elif len(p1) > 0 and len(p2) == 0: # one player
			query = {'$and': [{'$or': [{'Winner': {'$regex': p1, '$options': 'i'}},
							 {'Loser': {'$regex': p1, '$options': 'i' }}]},
							 {'Surface': {'$regex': surface, '$options': 'i'}},
							 {'Location': {'$regex': location, '$options': 'i'}},
							 {'Date': {'$regex': '.*' + years + '.*', '$options': 'i'}}]}
			route = 2
		elif len(p1) == 0 and len(p2) == 0 and (len(surface) > 0 or len(location) > 0 or len(years) > 0):
			query = {'$and': [{'Surface': {'$regex': surface}},
							  {'Location': {'$regex': location, '$options': 'i'}},
							  {'Date': {'$regex': '.*' + years + '.*', '$options': 'i'}}]}
			route = 3

		results = pd.DataFrame(list(collection.find(query)))
		if len(results) > 0:
			results['Date'] = pd.to_datetime(results['Date'], format = '%m/%d/%Y')
			results = results.sort_values('Date', ascending = False)
			results['Date'] = results['Date'].dt.strftime('%m/%d/%Y')
		else:
			abort(404)

		if route == 1:
			return render_template('results1.html', 
									data = results, 
									name1 = p1, 
									name2 = p2, 
									surface = surface,
									location = location,
									year = years,
									years = map(str, range(2005, 2022)),
									np = np,
									pd = pd,
									p1 = results[results['Winner'].str.upper() == (p1.upper())],
									p2 = results[results['Winner'].str.upper() == (p2.upper())])
		elif route == 2:
			return render_template('results2.html', 
									data = results,
									name1 = p1,
									np = np,
									pd = pd,
									location = location,
									year = years,
									years = map(str, range(2005, 2022)),
									surface = surface,
									p1_win = results[results['Winner'].str.upper() == (p1.upper())],
									p1_loss = results[results['Loser'].str.upper() == (p1.upper())])
		elif route == 3:
			return render_template('results3.html',
									data = results,
									surface = surface,
									location = location,
									year = years,
									years = map(str, range(2005, 2022)),
									np = np,
									pd = pd)
		else:
			abort(401)
	elif request.method == 'GET':
		loc = location
		p1 = player

		if p1 is not None:
			query = {'$or': [{'Winner': {'$regex': player, '$options': 'i'}}, {'Loser': {'$regex': player, '$options': 'i'}}]}
			results = pd.DataFrame(list(collection.find(query)))
			results['Date'] = pd.to_datetime(results['Date'], format = '%m/%d/%Y')
			results = results.sort_values('Date', ascending = False)
			results['Date'] = results['Date'].dt.strftime('%m/%d/%Y')

			return render_template('results2.html', 
										data = results,
										name1 = p1,
										np = np,
										pd = pd,
										years = map(str, range(2005, 2022)),
										p1_win = results[results['Winner'].str.upper() == (p1.upper())],
										p1_loss = results[results['Loser'].str.upper() == (p1.upper())])
		elif loc is not None:
			query = {'Location': loc}
			results = pd.DataFrame(list(collection.find(query)))
			results['Date'] = pd.to_datetime(results['Date'], format = '%m/%d/%Y')
			results = results.sort_values('Date', ascending = False)
			results['Date'] = results['Date'].dt.strftime('%m/%d/%Y')
			return render_template('results3.html', 
										data = results,
										name1 = p1,
										np = np,
										pd = pd,
										location = location,
										surface = "",
										years = map(str, range(2005, 2022)))

	else:
		abort(404)


@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.template_filter()
def number_format(number):
	return format(int(number), ',d')

@app.template_filter()
def round_number(number):
	return round(number, 2)

def handle_404():
	return '404'

def handle_200():
	return '500'

app.register_error_handler(404, handle_404)
app.register_error_handler(500, handle_200)