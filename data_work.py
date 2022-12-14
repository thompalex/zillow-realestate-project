import pandas as pd
import numpy_financial as npf
import http.client, urllib.parse
import json
import os
from search import Limit
import yaml
import re
import datetime

# Format a number into a dollar amount
def format_money(amount):
    formatted_val = '${:,.2f}'.format(abs(amount))
    if round(amount, 2) < 0:
        return f'-{formatted_val}'
    return formatted_val

# Use this function to get a list of all unique neighborhoods in the zillow data
def get_unique_neighborhoods(dataset):
    unique_neighborhoods = set()
    df_with_unique = pd.DataFrame(columns=['Neighborhood', 'City', 'State'])
    length = len(df_with_unique)
    for t in dataset.itertuples():
        if t[1] not in unique_neighborhoods:
            unique_neighborhoods.add(t[1])
            df_with_unique.loc[length] = [t[2], t[4], t[9]]
            length += 1
    # Output the unique neighborhoods to this file
    df_with_unique.to_csv("data/other/unique_neighborhoods.csv")

def add_latlon():
    # Connect to positionstack api
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
    # Load in list of unique neighborhoods
    unique_neighborhoods = pd.read_csv('data/other/unique_neighborhoods.csv')
    # Query positionstack for the latlon of each neighborhood
    unique_neighborhoods['latlon'] = unique_neighborhoods.apply(lambda x: get_geocode(x['Neighborhood'], x['City'], x['State']), axis=1)
    unique_neighborhoods.to_csv('data/other/unique_neighborhoods_with_latlon.csv')



def add_zipcodes():
    def get_zipcode(latlon):
        # Connect to positionstack api
        positionstack_key = os.getenv('POSITIONSTACK_KEY2')
        conn = http.client.HTTPConnection('api.positionstack.com')
        # Create parameters
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
    # Open the set of neighborhoods with latlons
    unique_neighborhoods_w_latlon = pd.read_csv('data/other/unique_neighborhoods_with_latlon.csv')
    # Get zipcodes from positionstack using latlons
    unique_neighborhoods_w_latlon['zipcode'] = unique_neighborhoods_w_latlon.apply(lambda x: get_zipcode(x['latlon']), axis=1)
    unique_neighborhoods_w_latlon.to_csv('data/other/unique_neighborhoods_w_zip_latlon.csv')

# Create zipcode mapping using the positionstack api
def create_zipcode_mapping(dataset):
    # Create zipcode mapping starting with our zillow data
    get_unique_neighborhoods(dataset)
    add_latlon()
    add_zipcodes()

# Find the latest date in a list of dates
def find_latest_date(dates):
    dates = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in dates if '20' in x]
    return str(max(dates).date())

def merge_zillow_data(arg_format):
    # Get the options for numbers of beds and merge their files in
    list_numbeds = arg_format['beds']['data'].keys()
    # Concatenate each of the csvs that correspond to individual bedroom amounts
    arr = []
    for i in list_numbeds:
        nd = pd.read_csv(f'data/zillow_data/{i}_bedroom.csv')
        pricecol = find_latest_date(nd.columns)
        nd['Price'] = nd[pricecol]
        nd = nd[['RegionID', 'RegionName', 'State', 'City', 'Metro', 'Price']]
        nd['Beds'] = int(i)
        arr.append(nd)
    zillow_data = pd.concat(arr, axis=0)
    zillow_data = zillow_data[zillow_data['Price'].notna()]
    return zillow_data

# Generate the project dataset from the zillow files and the region mapping
def generate_dataset():
    # Get the format of the arguments to ensure that we get the right files
    arg_format = yaml.safe_load(open('config_param.yml', 'rb'))
    data_format = yaml.safe_load(open('config_data.yml', 'rb'))
    # Load in and combine zillow files
    zillow_data = merge_zillow_data(arg_format)
    # I highly recommend not ever deleting the mapping file since it would take around 6 hours to recreate, but this is here for completeness
    if not os.path.exists('data/other/unique_neighborhoods_w_zip_latlon.csv'):
        create_zipcode_mapping(zillow_data)
    # Open Neighborhood to latlon and zipcode mapping file
    zip_latlon_mapping = pd.read_csv('data/other/unique_neighborhoods_w_zip_latlon.csv', usecols=["Neighborhood","City","latlon","zipcode"])
    # Merge zipcodes and latlons with zillow data
    start_data = pd.merge(zip_latlon_mapping, zillow_data, left_on=['Neighborhood','City'], right_on=['RegionName', 'City'], left_index=False, right_index=False)
    # For each dataset in the configuration, add it to the project dataset
    for key in data_format:
        if key != "final":
            dataset_config = data_format[key]
            dataset = pd.read_csv(dataset_config['path'], usecols=dataset_config['cols_to_use'])
            start_data = pd.merge(start_data, dataset, left_on=dataset_config['left_on'], right_on=dataset_config['right_on'], how=dataset_config['how'])
    # Get the final configuration for the dataset and run any of the column name changes required
    final_config = data_format['final']
    for source, dest in final_config['reformatting']:
        start_data[source] = start_data[dest]
    # Perform final dataset formatting to omitt unneccessary columns
    end_data = start_data[final_config['final_cols']]
    end_data.to_csv('data/project_dataset.csv', index=False)


def filter_data(data, args, param_format):
    # For each parameter of user input in our configuration
    for key in param_format:
        comp_column = param_format[key]["col"]
        # If we are checking for equality or a range, then we can process the query here
        if param_format[key]["comp"] == "equal":
            match_item = param_format[key]['data'][args[key]]
            data = data[data[comp_column] == match_item]
        elif param_format[key]['comp'] == "range":
            bottom, top = param_format[key]['data'][args[key]]
            data = data.loc[(data[comp_column] >= bottom) & (data[comp_column] <= top)]
    # For these params, we just want to calculate the estimated monthly payment
    rate = param_format['rate']['data'][args['rate']]
    timeline = param_format['timeline']['data'][args['timeline']]
    data['Monthly Payment'] = data['Price'].apply(lambda x: format_money(-1 * npf.pmt(rate / 100 / 12, 12 * timeline,x)))
    return data
    
# Format the frontend output
def format_output(filtered_df):
    # Define cols to be shown to the frontend user
    frontend_cols = ['Neighborhood', 'City', 'State Name', 'Price', 'Monthly Payment', 'Price Change']
    # Format the numbers into money-like strings
    filtered_df['Price Change'] = filtered_df['Price Change'].apply(lambda x: format_money(x))
    filtered_df['Price'] = filtered_df['Price'].apply(lambda x: format_money(x))
    # Generate two tables and two dictionaries for output to the frontend
    res = [filtered_df.head(5)]
    N = len(filtered_df)
    if N >= 10:
        res.append(filtered_df.tail(5))
    elif N >= 5:
        res.append(filtered_df.tail(N - 5))
    else:
        res.append(pd.DataFrame(columns = frontend_cols))
    
    tables = [df.to_html(index=False, columns=frontend_cols, justify="left", classes='table my-auto') for df in res]
    dfs = [df.to_dict('records') for df in res]
    return tables, dfs, None

# Make a query from the frontend
def make_query(args):
    # If the necessary nd has not been generated yet, create it
    if not os.path.exists('data/project_dataset.csv'):
        generate_dataset()
    # Read in the compiled data
    data = pd.read_csv('data/project_dataset.csv').fillna(0)
    # Load in user arguments and check for errors in their input
    parameter = open('config_param.yml', 'rb')
    parameter = yaml.safe_load(parameter)
    queryLimit = Limit(**parameter)
    args, errorLog = queryLimit.check_param(args)
    if not args:
        return None, None, errorLog
    # Filter the data based on the user's arguments
    filtered_df = filter_data(data, args, parameter)
    # Calculate forecasted price changes
    filtered_df['Price Change'] = filtered_df.apply(lambda x: x['Price'] * x['forecast'] / 100, axis=1)
    # Sort the data based on the user's input
    if args['forecast'] == "False":
        filtered_df.sort_values(by=['Price'], ascending = False, inplace = True)
    else:
        filtered_df.sort_values(by=['Price Change'], ascending=False, inplace = True)
    return format_output(filtered_df)

### Test statements for these methods ###
if __name__ == '__main__':
    # generate_dataset() if not os.path.exists('data/project_dataset.csv') else None
    # result = make_query({
    #         'region': 'Northeast',
    #         'beds': "1",
    #         'price': '$1000000 - $1500000',
    #         'rate': '4%',
    #         'timeline': '30 years',
    #         'forecast': "True"
    #     })
    # print(result)
    merge_zillow_data({'beds': {'data':{"1":1}}})
