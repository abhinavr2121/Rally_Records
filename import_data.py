import pandas as pd
import numpy as np
from colorama import Fore, init
import datetime
import requests
import pymongo
from fuzzywuzzy import fuzz

init(autoreset = True)

client = pymongo.MongoClient("mongodb+srv://normal-user:7Pv02lHlo3Dzdxai@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
db = client.RacquetStats

last_updated = '2021-08-15'

print('Finding new matches since ' + last_updated + '...')

atp_url = 'http://www.tennis-data.co.uk/2021/2021.xlsx'
wta_url = 'http://www.tennis-data.co.uk/2021w/2021.xlsx'

def formatter(url, group):
	print('Downloading ' + group + ' file...')
	r = requests.get(url, allow_redirects = True)
	filename = 'data/new_' + group + '.xlsx'
	open(filename, 'wb').write(r.content)

	new_file = pd.read_excel(filename)
	new_file = new_file[new_file['Date'] > last_updated]
	print('There are ' + str(len(new_file)) + ' new matches.')

	return new_file

def find_different(dataset, group):
	collection = db.ATP
	if group == 'WTA':
		collection = db.WTA

	print('Finding mismatched or unrecognized names...')
	distinct_winners = pd.DataFrame(list(collection.distinct('Winner')))
	distinct_losers = pd.DataFrame(list(collection.distinct('Loser')))

	distinct_players = pd.concat([distinct_winners, distinct_losers])
	distinct_names = distinct_players[0].unique().tolist()

	new_data_winners = np.array(dataset['Winner'].unique())
	new_data_losers = np.array(dataset['Loser'].unique())
	new_data_players = np.concatenate([new_data_losers, new_data_winners])
	new_players = np.setdiff1d(new_data_players, distinct_names)

	dataset.loc[dataset['WRank'] == 'N/A', 'WRank'] = 0
	dataset.loc[dataset['LRank'] == 'N/A', 'LRank'] = 0

	print('Unrecognized names (' + group + '): ' + ', '.join(new_players))

	for n in new_players:
		max_ratio = 0
		matched_name = ''
		for p in distinct_names:
			r = fuzz.ratio(n, p)
			if r > max_ratio:
				max_ratio = r
				matched_name = p
		if max_ratio >= 90:
			print(Fore.GREEN + 'REPLACING ' + n + ' with best match, ' + matched_name + ' (' + str(max_ratio) + '%)...')
			dataset.loc[dataset['Winner'] == n, 'Winner'] = matched_name
			dataset.loc[dataset['Loser'] == n, 'Loser'] = matched_name
		else:
			print(Fore.YELLOW + n + ' partially matched ' + matched_name + '(' + str(max_ratio) + '%), NOT REPLACING.')

	return dataset

atp = formatter(atp_url, 'ATP')
wta = formatter(wta_url, 'WTA')

if len(atp) > 0:
	atp = find_different(atp, 'ATP')
if len(wta) > 0:
	wta = find_different(wta, 'WTA')

print('Outputting modified spreadsheets...')
atp.to_excel('data/modified_atp.xlsx')
wta.to_excel('data/modified_wta.xlsx')


print('Data check complete.')