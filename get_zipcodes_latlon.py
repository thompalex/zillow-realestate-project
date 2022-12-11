import pandas as pd
import http.client, urllib.parse
import json
import urllib
import numpy as np

def get_unique_neighborhoods():
    dataset = pd.read_csv("project_dataset.csv")
    unique_neighborhoods = set()
    df_with_unique = pd.DataFrame(columns=['Neighborhood', 'City', 'State'])
    length = len(df_with_unique)
    for t in dataset.itertuples():
        if t[1] not in unique_neighborhoods:
            unique_neighborhoods.add(t[1])
            df_with_unique.loc[length] = [t[2], t[4], t[9]]
            length += 1
    df_with_unique.to_csv("unique_neighborhoods.csv")

def add_latlon():
    conn = http.client.HTTPConnection('api.positionstack.com')
    # Function to get individual lon/lat
    def get_geocode(neighborhood, city,  state):
        params = urllib.parse.urlencode({
            'access_key': '3e6e9d79072006e5502b0ca27ec0a5bf',
            'query': f'{neighborhood}, {city}' ,
            'region': state,
            'country': 'US',
            'limit': 1,
        })
        conn.request('GET', '/v1/forward?{}'.format(params))
        res = conn.getresponse()
        api_result = json.loads(res.read().decode('utf-8'))
        print(api_result)
        if 'data' in api_result and len(api_result['data']) > 0 and api_result['data'][0] != []:
            return f'{api_result["data"][0]["latitude"]}, {api_result["data"][0]["longitude"]}'
        else:
            return ""
    unique_neighborhoods = pd.read_csv('unique_neighborhoods.csv')
    unique_neighborhoods['latlon'] = unique_neighborhoods.apply(lambda x: get_geocode(x['Neighborhood'], x['City'], x['State']), axis=1)
    unique_neighborhoods.to_csv('unique_neighborhoods_with_latlon.csv')



def add_zipcodes():
    def get_zipcode(latlon):
        conn = http.client.HTTPConnection('api.positionstack.com')

        params = urllib.parse.urlencode({
            'access_key': 'b552a752eb62669868c9126f52d87eb4',
            'query': latlon,
            })
        conn.request('GET', '/v1/reverse?{}'.format(params))

        res = conn.getresponse()
        data = json.loads(res.read().decode('utf-8'))
        try:
            if data['data'][0]['postal_code']:
                print(data['data'][0]['postal_code'][:5])
                return data['data'][0]['postal_code'][:5]
            else:
                return ""
        except:
            return ""
    unique_neighborhoods_w_latlon = pd.read_csv('unique_neighborhoods_with_latlon.csv')
    unique_neighborhoods_w_latlon['zipcode'] = unique_neighborhoods_w_latlon.apply(lambda x: get_zipcode(x['latlon']), axis=1)
    unique_neighborhoods_w_latlon.to_csv('unique_neighborhoods_w_zip_latlon.csv')

# add_latlon()
add_zipcodes()

