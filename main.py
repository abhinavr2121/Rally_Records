import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import plotly.express as px
import datetime
import pymongo
import math

st.set_page_config(layout="wide")

def safe_divide(n, m):
    if m == 0:
        return 0
    return round(n / m, 2)

with st.sidebar:
    st.title('RallyRecords')
    st.subheader('WTA and ATP data analysis')
    mode = st.selectbox(label = 'Mode (Women\'s WTA or Men\'s ATP)', options = ('ATP', 'WTA'))

    client = pymongo.MongoClient("mongodb+srv://normal-user:7Pv02lHlo3Dzdxai@cluster0.ro0mt.mongodb.net/RacquetStats?retryWrites=true&w=majority")
    db = client.RacquetStats

    stats_collection = db.Stats

    collection = db[mode]
    countries = pd.read_csv('data/countries.csv')
    p1 = st.selectbox(label = 'Player 1', options = countries.loc[countries['Division'] == mode, 'Name'].sort_values().unique().tolist())
    p2 = st.selectbox(label = 'Player 2', options = countries.loc[countries['Division'] == mode, 'Name'].sort_values().unique().tolist())

    st.write('Data is available from 2005 (ATP) and 2007 (WTA).')
if p1 == p2:
    st.warning("You've selected the same player for both inputs!")

query = {'$and': []}
if p1 is not None and p2 is not None:
    query['$and'].append({'Winner': {'$regex': p1 + '|' + p2, '$options': 'i'}})
    query['$and'].append({'Loser': {'$regex': p1 + '|' + p2, '$options': 'i'}})
    p1_query = {'$or': [{'Winner': {'$regex': p1, '$options': 'i'}}, {'Loser': {'$regex': p1, '$options': 'i'}}]}
    p2_query = {'$or': [{'Winner': {'$regex': p2, '$options': 'i'}}, {'Loser': {'$regex': p2, '$options': 'i'}}]}

results = pd.DataFrame(list(collection.find(query))).reset_index(drop = True)
p1_results = pd.DataFrame(list(collection.find(p1_query))).reset_index(drop = True)
p2_results = pd.DataFrame(list(collection.find(p2_query))).reset_index(drop = True)
p1_results['Date'] = pd.to_datetime(p1_results['Date'], infer_datetime_format = True)
p2_results['Date'] = pd.to_datetime(p2_results['Date'], infer_datetime_format = True)
p1_results = p1_results.sort_values(by = 'Date')
p2_results = p2_results.sort_values(by = 'Date')

p1_results.loc[(p1_results['WRank'] == ''), 'WRank'] = np.nan
p2_results.loc[(p2_results['WRank'] == ''), 'WRank'] = np.nan
p1_results.loc[(p1_results['LRank'] == ''), 'LRank'] = np.nan
p2_results.loc[(p2_results['LRank'] == ''), 'LRank'] = np.nan

if results.shape[0] == 0:
    st.error("These players have never played before!")
else:
    results = results.drop(columns = '_id', axis = 1)
    results_display = results
    results_display['Set 1'] = (results_display['W1'].astype(str).str.cat(results_display['L1'].astype(str), sep = '-'))
    results_display['Set 2'] = (results_display['W2'].astype(str).str.cat(results_display['L2'].astype(str), sep = '-'))
    results_display['Set 3'] = (results_display['W3'].astype(str).str.cat(results_display['L3'].astype(str), sep = '-'))
    if mode == 'ATP':
        results_display['Set 4'] = (results_display['W4'].astype(str).str.cat(results_display['L4'].astype(str), sep = '-'))
        results_display['Set 5'] = (results_display['W5'].astype(str).str.cat(results_display['L5'].astype(str), sep = '-'))
    else:
        results_display['Set 4'] = ' '
        results_display['Set 5'] = ' '

    st.header('Player Comparison')
    st.text('')
    col1, col2 = st.columns(2)
    with col1:
        p1_flag = countries.loc[countries['Name'] == p1, 'Code'].item()
        p1_code = countries.loc[countries['Name'] == p1, '3Code'].item()
        st.image('https://countryflagsapi.com/svg/' + p1_flag, width = 50)
        st.subheader(countries.loc[countries['Name'] == p1, 'First'].item() + ' ' + p1.rpartition(' ')[0] + ' (' + p1_code + ')')
        wins = p1_results.loc[p1_results['Winner'] == p1].shape[0]
        losses = p1_results.loc[p1_results['Loser'] == p1].shape[0]
        upsets_1 = p1_results.loc[np.logical_and(p1_results['Winner'] == p1, p1_results['WRank'] > p1_results['LRank'])].shape[0]
        upsets_2 = p1_results.loc[np.logical_and(p1_results['Loser'] == p1, p1_results['LRank'] < p1_results['WRank'])].shape[0]

        st.write(str(wins) + ' - ' + str(losses) + ' (' + str(safe_divide(100 * wins, wins + losses)) + '% win rate)')
        st.write(str(upsets_1) + ' career wins against higher ranking players.')
        st.write(str(upsets_2) + ' career losses against lower ranking players.')

        tournament_df = p1_results.loc[np.logical_and(p1_results['Winner'] == p1, p1_results['Round'] == 'The Final')].groupby('Tournament').count()
        tournament_df['T'] = tournament_df.index
        tournament_df.reset_index(drop = True, inplace = True)
        fig = px.pie(tournament_df, values = 'Round', names = 'T', title = 'Title Breakdown', color_discrete_sequence= px.colors.sequential.Plasma_r, width = 500, labels = dict(T = 'Tournament', Round = 'Titles'))
        fig.update_traces(textposition='inside', textinfo='label')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)
    with col2:
        p2_flag = countries.loc[countries['Name'] == p2, 'Code'].item()
        p2_code = countries.loc[countries['Name'] == p2, '3Code'].item()
        st.image('https://countryflagsapi.com/svg/' + p2_flag, width = 50)
        st.subheader(countries.loc[countries['Name'] == p2, 'First'].item() + ' ' + p2.rpartition(' ')[0] + ' (' + p2_code + ')')
        wins = p2_results.loc[p2_results['Winner'] == p2].shape[0]
        losses = p2_results.loc[p2_results['Loser'] == p2].shape[0]
        upsets_1 = p2_results.loc[np.logical_and(p2_results['Winner'] == p2, p2_results['WRank'] > p2_results['LRank'])].shape[0]
        upsets_2 = p2_results.loc[np.logical_and(p2_results['Loser'] == p2, p2_results['LRank'] < p2_results['WRank'])].shape[0]

        st.write(str(wins) + ' - ' + str(losses) + ' (' + str(safe_divide(100 * wins, wins + losses)) + '% win rate)')
        st.write(str(upsets_1) + ' career wins against higher ranking players.')
        st.write(str(upsets_2) + ' career losses against lower ranking players.')

        tournament_df = p2_results.loc[np.logical_and(p2_results['Winner'] == p2, p2_results['Round'] == 'The Final')].groupby('Tournament').count()
        tournament_df['T'] = tournament_df.index
        tournament_df.reset_index(drop = True, inplace = True)
        fig = px.pie(tournament_df, values = 'Round', names = 'T', title = 'Title Breakdown', width = 500, color_discrete_sequence= px.colors.sequential.Plasma_r, labels = dict(T = 'Tournament', Round = 'Titles'))
        fig.update_traces(textposition='inside', textinfo='label')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig)

    p1_results['ranks'] = np.where(p1_results['Winner'] == p1, p1_results['WRank'], p1_results['LRank'])
    p1_results['name'] = p1
    p2_results['ranks'] = np.where(p2_results['Winner'] == p2, p2_results['WRank'], p2_results['LRank'])
    p2_results['name'] = p2
    new_df = pd.concat([p1_results[['Date', 'ranks', 'name']], p2_results[['Date', 'ranks', 'name']]], axis = 0)
    fig = px.line(new_df, x  = 'Date', y = 'ranks', title = 'Performance', color_discrete_sequence= px.colors.qualitative.Bold, color = 'name', width = 1000, labels = dict(ranks = 'Singles Ranking', name = 'Player'))
    fig.update_traces(line = dict(width = 3))
    st.plotly_chart(fig)

    st.header('Head to Head')
    st.write(p1 + ' and ' + p2 + ' have played ' + str(results.shape[0]) + ' matches, of which ' + p1 + ' has won ' + str(results.loc[results['Winner'] == p1].shape[0]) + ' and ' + p2 + ' has won ' + str(results.loc[results['Winner'] == p2].shape[0]) + '.')

    def plot_item(item, w, g = False):
        index = results[item].unique()
        location = []
        num_wins = []
        person = []
        for i in index:
            if i == '-':
                continue
            location.append(i)
            num_wins.append(results.loc[np.logical_and(results[item] == i, results['Winner'] == p1)].shape[0])
            person.append(p1)
            location.append(i)
            num_wins.append(results.loc[np.logical_and(results[item] == i, results['Winner'] == p2)].shape[0])
            person.append(p2)
        win_df = pd.DataFrame(data = {item: location, 'num_wins': num_wins, 'person': person})
        barmode = 'stack'
        if g:
            barmode = 'group'
        fig = px.bar(win_df, x = item, y = num_wins, color_discrete_sequence= px.colors.qualitative.Bold, barmode = barmode, height = 400, width = w, color = person, template = 'plotly_dark',
        labels = dict(locations = item, y = 'Wins', color = 'Player'))
        st.plotly_chart(fig)

    with st.expander('LOCATION INSIGHTS'):
        plot_item('Location', 900)
        st.subheader('Top Spots:')
        st.write(p1 + ' and ' + p2 + ' have played in ' + str(results.groupby(by = 'Location').count()['Round'].sort_values().tail(1).index.item()) + ' the most times.')
    with st.expander('SURFACE INSIGHTS'):
        plot_item('Surface', 1000, True)
    with st.expander('ROUND INSIGHTS'):
        plot_item('Round', 1000, True)
    with st.expander('SET INSIGHTS'):
        plot_item('Set 1', 800)
        p1_first_set_wins = results.loc[np.logical_and(results['W1'] > results['L1'], results['Winner'] == p1)].shape[0]
        p1_first_set_losses = results.loc[np.logical_and(results['L1'] > results['W1'], results['Loser'] == p1)].shape[0]
        p2_first_set_wins = results.loc[np.logical_and(results['W1'] > results['L1'], results['Winner'] == p2)].shape[0]
        p2_first_set_losses = results.loc[np.logical_and(results['L1'] > results['W1'], results['Loser'] == p2)].shape[0]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Starting Strong:')
            st.write('After winning the first set, ' + p1 + ' won ' + str(safe_divide(100 * p1_first_set_wins, p1_first_set_wins + p1_first_set_losses)) + '% of the time and ' + p2 + ' won ' + str(safe_divide(100 * p2_first_set_wins, p2_first_set_wins + p2_first_set_losses)) + '% of the time.')
        with col2:
            st.subheader('Clutching Out:')
            subset_1 = results.loc[np.logical_and(results['Tournament'] == 'Grand Slam', results['Wsets'] + results['Lsets'] == 5)]
            subset_2 = results.loc[np.logical_and(results['Tournament'] != 'Grand Slam', results['Wsets'] + results['Lsets'] == 3)]
            subset = pd.concat([subset_1, subset_2])
            st.write('In final set situations, ' + p1 + ' won ' + str(safe_divide(100 * subset.loc[subset['Winner'] == p1].shape[0], subset.shape[0])) + '% of the time and ' + p2 + ' won ' + str(safe_divide(100 * subset.loc[subset['Winner'] == p2].shape[0], subset.shape[0])) + '% of the time.')

    with st.expander("RAW HISTORICAL DATA"):
        results_display['Date'] = pd.to_datetime(results_display['Date'], infer_datetime_format = True)
        if mode == 'ATP':
            st.table(results_display[['Date', 'Location', 'Tournament', 'Court', 'Surface', 'Round', 'Winner', 'Loser', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5', 'Comment']].astype(str).sort_values(by = 'Date', ascending = False).reset_index(drop = True))
        else:
            st.table(results_display[['Date', 'Location', 'Tournament', 'Court', 'Surface', 'Round', 'Winner', 'Loser', 'Set 1', 'Set 2', 'Set 3', 'Comment']].astype(str).sort_values(by = "Date", ascending = False).reset_index(drop = True))
    st.write('Data may contain a few inaccuracies. Sourced from Tennis-Data.co.uk.')
    st.write('Contained data spans 2005 - 2022. Last updated June 22nd, 2022.')
