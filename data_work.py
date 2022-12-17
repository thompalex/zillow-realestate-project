import pandas as pd
import numpy_financial as npf
import http.client, urllib.parse
import json
import os
from search import Limit
import yaml

# This is where the actual data stuff is done for the most part
def get_unique_neighborhoods(dataset):
    unique_neighborhoods = set()
    df_with_unique = pd.DataFrame(columns=['Neighborhood', 'City', 'State'])
    length = len(df_with_unique)
    for t in dataset.itertuples():
        if t[1] not in unique_neighborhoods:
            unique_neighborhoods.add(t[1])
            df_with_unique.loc[length] = [t[2], t[4], t[9]]
            length += 1
    df_with_unique.to_csv("data/other/unique_neighborhoods.csv")

def add_latlon():
    positionstack_key = os.getenv('POSITIONSTACK_KEY1')
    conn = http.client.HTTPConnection('api.positionstack.com')
    # Function to get individual lon/lat
    def get_geocode(neighborhood, city,  state):
        params = urllib.parse.urlencode({
            'access_key': positionstack_key,
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
    unique_neighborhoods = pd.read_csv('data/other/unique_neighborhoods.csv')
    unique_neighborhoods['latlon'] = unique_neighborhoods.apply(lambda x: get_geocode(x['Neighborhood'], x['City'], x['State']), axis=1)
    unique_neighborhoods.to_csv('data/other/unique_neighborhoods_with_latlon.csv')



def add_zipcodes():
    def get_zipcode(latlon):
        positionstack_key = os.getenv('POSITIONSTACK_KEY2')
        conn = http.client.HTTPConnection('api.positionstack.com')
        params = urllib.parse.urlencode({
            'access_key': positionstack_key,
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
    unique_neighborhoods_w_latlon = pd.read_csv('data/other/unique_neighborhoods_with_latlon.csv')
    unique_neighborhoods_w_latlon['zipcode'] = unique_neighborhoods_w_latlon.apply(lambda x: get_zipcode(x['latlon']), axis=1)
    unique_neighborhoods_w_latlon.to_csv('data/other/unique_neighborhoods_w_zip_latlon.csv')

def create_zipcode_mapping(dataset):
    get_unique_neighborhoods(dataset)
    add_latlon()
    add_zipcodes()

def merge_zillow_data(arg_format):
    list_numbeds = arg_format['beds']['data']
    # Concatenate each of the csvs that correspond to individual bedroom amounts
    arr = []
    for i in list_numbeds:
        nd = pd.read_csv(f'data/zillow_data/{i}_bedroom.csv')
        nd = nd[['RegionID', 'RegionName', 'State', 'City', 'Metro', '2022-10-31']]
        nd['bedrooms'] = int(i)
        arr.append(nd)
    zillow_data = pd.concat(arr, axis=0)
    return zillow_data

# Generate the project dataset from the zillow files and the region mapping
def generate_dataset():
    arg_format = yaml.safe_load(open('config_param.yml', 'rb'))
    region_mapping = pd.read_csv('data/other/states.csv')
    price_forecasts = pd.read_csv('data/zillow_data/pricing_forecast.csv', usecols=["RegionName", "2023-10-31"])
    # Load in and combine zillow files
    zillow_data = merge_zillow_data(arg_format)
    # I highly recommend not ever deleting the mapping file since it would take around 6 hours to recreate, but this is here for completeness
    if not os.path.exists('data/other/unique_neighborhoods_w_zip_latlon.csv'):
        create_zipcode_mapping(zillow_data)
    # Open Neighborhood to latlon and zipcode mapping file
    zip_latlon_mapping = pd.read_csv('data/other/unique_neighborhoods_w_zip_latlon.csv')
    # Merge with region mapping to get region name
    data_with_region = pd.merge(zillow_data, region_mapping, left_on="State", right_on="State")
    # Merge zipcodes and latlons with zillow data
    data_w_zip_latlon = pd.merge(zip_latlon_mapping, data_with_region, left_on=['Neighborhood', 'State', 'City'], right_on=['RegionName', 'State Name', 'City'])
    # Merge price forecasts into project dataset
    complete_df = pd.merge(data_w_zip_latlon, price_forecasts, left_on='zipcode', right_on='RegionName', how='left')
    # Reformat dataset
    complete_df['price'] = complete_df['2022-10-31']
    complete_df['state'] = complete_df['State_y']
    complete_df['zipcode'] = complete_df['RegionName_y']
    complete_df['forecast'] = complete_df['2023-10-31']
    complete_df = complete_df[['Neighborhood','latlon','zipcode','RegionID','state','City','Metro','price','bedrooms','Region','State Name', 'forecast']]
    complete_df.to_csv('data/project_dataset.csv', index=False)


def filter_data(data, args):
    beds = int(args['beds'])
    region = args['region'] 
    timeline = int(args['timeline'].split()[0])
    rate = sum([int(x.strip().replace('%','')) for x in args['rate'].split('-')]) / 2
    price = tuple([int(x.strip(' $').replace(',', '')) for x in args['price'].split('-')])
    # Each of the four following lines filters out results that do not adhere to the inputs
    with_region = data[data['Region'] == region]
    with_bedrooms = with_region[with_region['bedrooms'] == beds]
    bottom_price, top_price = price
    with_all = with_bedrooms.loc[(with_bedrooms['price'] >= bottom_price) & (with_bedrooms['price']  <= top_price)].copy()
    # Get mortgage rate and timeline to calculate monthly payment using numpy_financial
    with_all['Monthly Payment'] = with_all['price'].apply(lambda x: f'${round(-1 * npf.pmt(rate / 100 / 12, 12 * timeline,x), 2):,.2f}')
    return with_all
    

# Make a query from the frontend
def make_query(args):
    # If the necessary nd has not been generated yet, create it
    if not os.path.exists('data/project_dataset.csv'):
        generate_dataset()
    # Read in the compiled data
    data = pd.read_csv('data/project_dataset.csv').fillna(0)
    parameter = open('config_param.yml', 'rb')
    parameter = yaml.safe_load(parameter)
    queryLimit = Limit(**parameter)
    args, errorLog = queryLimit.check_param(args)
    if not args:
        return None, None, errorLog
    filtered_df = filter_data(data, args)
    # Calculate forecasted price changes
    filtered_df['price_change'] = filtered_df.apply(lambda x: x['price'] * x['forecast'] / 100, axis=1)
    if args['forecast'] == "False":
        filtered_df.sort_values(by=['price'], ascending = False, inplace = True)
    else:
        filtered_df.sort_values(by=['price_change'], ascending=False, inplace = True)
    filtered_df['Price Change'] = filtered_df['price_change'].apply(lambda x: f'${x:,.2f}')
    filtered_df['Price'] = filtered_df['price'].apply(lambda x: f'${x:,.2f}')
    filtered_df['Beds'] = filtered_df['bedrooms']
    filtered_df['Zipcode'] = filtered_df['zipcode']
    filtered_df = filtered_df[['Neighborhood', 'Zipcode', 'City', 'State Name', 'Price', 'Monthly Payment', 'Price Change', 'latlon']]
    res = [filtered_df.head(5), filtered_df.tail(5)]
    tables = [df.to_html(index=False, columns=['Neighborhood', 'Zipcode', 'City', 'State Name', 'Price', 'Monthly Payment', 'Price Change'], justify="left", classes='table my-auto') for df in res]
    dfs = [df.to_dict('records') for df in res]
    return tables, dfs, None

### Test statements for these methods ###
if __name__ == '__main__':
    generate_dataset() if not os.path.exists('data/project_dataset.csv') else None
    result = make_query({
            'region': 'Northeast',
            'beds': "1",
            'price': '800,000 - $1,000,000',
            'rate': '4% - 5%',
            'timeline': '30 years',
            'forecast': True
        })

    print(result)