from flask import Flask, render_template, request, abort, redirect, url_for
import pymongo
import pandas as pd
import json
import time
import datetime
import re
import math
import numpy as np
import os

app = Flask(__name__)

client = pymongo.MongoClient("mongodb+srv://normal-user:7Pv02lHlo3Dzdxai@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
db = client.RacquetStats

stats_collection = db.Stats

collection = db.ATP
countries = pd.read_csv('data/countries.csv')

distinct_locations = pd.concat([pd.DataFrame(list(db.ATP.distinct('Location'))), 
					 pd.DataFrame(list(db.WTA.distinct('Location')))])[0].unique().tolist()
distinct_names = countries['Name'].unique().tolist()
distinct_years = list(range(2005, 2022))
distinct_countries = countries['Country'].unique().tolist()
distinct_surfaces = ['Hard', 'Clay', 'Grass', 'Carpet']


@app.route('/')
def main_root():
	return render_template('index.html', 
							names = distinct_names, 
							surface = distinct_surfaces,
							locations = distinct_locations,
							countries = distinct_countries)

@app.route('/process/', methods = ['POST'])
def create_url():
	group = request.form.get('data-source')
	p1 = request.form.get('p1')
	p2 = request.form.get('p2')
	surface = request.form.get('surface')
	location = request.form.get('location')
	country = request.form.get('country')
	year = request.form.get('year')
	
	p1 = set_none(p1)
	p2 = set_none(p2)
	surface = set_none(surface)
	location = set_none(location)
	country = set_none(country)
	year = set_none(year)

	url = '/results' + '/group=' + group + '/p1=' + p1 + '/p2=' + p2 + '/surface=' + surface + '/location=' + location + '/country=' + country + '/year=' + year
	
	return redirect(url)


@app.route('/results/group=<group>/p1=<p1>/p2=<p2>/surface=<surface>/location=<location>/country=<country>/year=<year>/')
def results(group, p1, p2, surface, location, country, year):

	stat_obj = {"timestamp": datetime.datetime.now()}
	arb = stats_collection.insert_one(stat_obj)

	mode = 'ATP'
	if group == 'WTA':
		collection = db.WTA
		mode = 'WTA'
	else:
		collection = db.ATP
		mode = 'ATP'
		
	p1 = check_none(p1)
	p2 = check_none(p2)
	surface = check_none(surface)
	location = check_none(location)
	country = check_none(country)
	year = check_none(year)

	query = {'$and': []}

	if p1 is not None and p2 is not None:
		query['$and'].append({'Winner': {'$regex': p1 + '|' + p2, '$options': 'i'}})
		query['$and'].append({'Loser': {'$regex': p1 + '|' + p2, '$options': 'i'}})

	elif p1 is not None and p2 is None:
		query['$and'].append({'$or': [
								{'Winner': {'$regex': p1, '$options': 'i'}},
								{'Loser': {'$regex': p1, '$options': 'i' }}
							]})

	if any(l is not None for l in [surface, location, country, year]):
		if surface is not None:
			query['$and'].append({'Surface': {'$regex': surface, '$options': 'i'}})
		
		if location is not None:
			query['$and'].append({'Location': {'$regex': location, '$options': 'i'}})

		if year is not None:
			query['$and'].append({'Date': {'$regex': '.*' + str(year) + '.*', '$options': 'i'}})

		if country is not None and p1 is None:
			query = {}

	results = pd.DataFrame(list(collection.find(query)))
	nationality = countries.Name.values
	if country is not None:
		nationality = countries[countries['Country'] == country].Name.values
		if p1 is not None:
			nationality_cap = [s.upper() for s in nationality]
			if p1.upper() in nationality_cap:
				rem = nationality_cap.index(p1.upper())
				nationality = np.delete(nationality, rem)
		results = results[results['Winner'].isin(nationality) | results['Loser'].isin(nationality)]

	if len(results) == 0:
		abort(404)
	
	results['Date'] = pd.to_datetime(results['Date'], format = '%m/%d/%Y')
	results = results.sort_values('Date', ascending = False)
	results['Date'] = results['Date'].dt.strftime('%m/%d/%Y')

	tailored_locations = results['Location'].value_counts()
	tailored_years = pd.to_datetime(results['Date'], format = '%m/%d/%Y').dt.year.value_counts().index

	first_name = 'none'
	last_name = 'none'
	if p1 is not None and p2 is None:
		space_index = [m.start() for m in re.finditer(" ", p1.upper())][-1]
		last_name = p1[:space_index]
		first_name = countries[countries['Name'].str.upper() == p1.upper()].First.values[0]

	p1 = set_none(p1)
	p2 = set_none(p2)
	surface = set_none(surface)
	location = set_none(location)
	country = set_none(country)
	year = set_none(year)

	return render_template('results.html',
		data = results,
		distinct_surfaces = distinct_surfaces,
		distinct_locations = tailored_locations.index.tolist(),
		distinct_years = np.sort(tailored_years),
		referrer = request.headers.get('Referer'),
		name1 = p1,
		name2 = p2,
		surface = surface,
		location = location,
		mode = mode,
		year = year,
		country = country,
		countries = countries,
		years = map(str, range(2005, 2022)),
		np = np,
		pd = pd,
		math = math,
		p1 = results[results['Winner'].str.upper() == (p1.upper())],
		p2 = results[results['Winner'].str.upper() == (p2.upper())],
		first_name = first_name,
		last_name = last_name,
		p1_win = results[results['Winner'].str.upper() == (p1.upper())],
		p1_loss = results[results['Loser'].str.upper() == (p1.upper())],
		nationality = nationality,
		time = time)

@app.route('/group/<group>/player/<player>/', methods = ['GET'])
def reroute(group, player):
	url = '/results' + '/group=' + group + '/p1=' + player + '/p2=none/surface=none/location=none/country=none/year=none/'
	return redirect(url)

@app.route('/about')
def serve_about():
	return render_template('about.html')

@app.route('/changelog')
def serve_changelog():
	return render_template('changelog.html')

@app.after_request
def add_header(response):
	response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	response.headers['Cache-Control'] = 'public, max-age=0'
	return response

@app.template_filter()
def debug(text):
	print(text)
	return ''

@app.template_filter()
def number_format(number):
	return format(int(number), ',d')

@app.template_filter()
def round_number(number):
	return round(number, 2)

def handle_401(e):
	return render_template('errors.html',
							message = 'No parameters were entered.',
							referrer = request.headers.get('Referer'))

def handle_404(e):
	return render_template('errors.html',
							message = 'There were no "matches" for those parameters!',
							referrer = request.headers.get('Referer'))

def handle_500(e):
	return render_template('errors.html',
							message = "Something went wrong. It's our fault, not yours.",
							referrer = request.headers.get('Referer'))

def set_none(variable):
	if variable is None or len(variable) == 0:
		return 'none'
	else:
		return variable

def check_none(variable):
	if variable == 'none':
		return None
	else:
		return variable

app.register_error_handler(401, handle_401)
app.register_error_handler(404, handle_404)
app.register_error_handler(500, handle_500)

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	app.run(host = '0.0.0.0', port = port)