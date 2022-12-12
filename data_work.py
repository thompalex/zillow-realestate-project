import pandas as pd
import numpy_financial as npf
import http.client, urllib.parse
import json
import os

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


# Generate the project nd from the zillow files and the region mapping
def generate_dataset():
    region_mapping = pd.read_csv('data/other/states.csv')
    # Concatenate each of the csvs that correspond to individual bedroom amounts
    arr = []
    for i in range(1, 6):
        nd = pd.read_csv(f'data/zillow_data/{i}_bedroom.csv')
        nd = nd[['RegionID', 'RegionName', 'State', 'City', 'Metro', '2022-10-31']]
        nd['bedrooms'] = i
        arr.append(nd)
    zillow_data = pd.concat(arr, axis=0)
    # Merge with region mapping to get region name
    data_with_region = pd.merge(zillow_data, region_mapping, left_on="State", right_on="State")
    # Drop unnecessary columns
    data_with_region = data_with_region[['RegionID', 'RegionName', 'State', 'City', 'Metro', '2022-10-31', 'bedrooms', 'Region', 'State Name']]
    # Reset the indicies and save the DF to a csv
    data_with_region.reset_index()
    # I highly recommend not ever deleting the mapping file since it would take around 6 hours to recreate, but this is here for completeness
    if not os.path.exists('data/other/unique_neighborhoods_w_zip_latlon.csv'):
        create_zipcode_mapping(data_with_region)
    # Open Neighborhood to latlon and zipcode mapping file
    zip_latlon_mapping = pd.read_csv('data/other/unique_neighborhoods_w_zip_latlon.csv')
    # Merge zipcodes and latlons with zillow data
    data_w_zip_latlon = pd.merge(zip_latlon_mapping, data_with_region, left_on=['Neighborhood', 'State', 'City'], right_on=['RegionName', 'State Name', 'City'])
    # Format data nicely
    data_w_zip_latlon['State'] = data_w_zip_latlon['State_y']
    data_w_zip_latlon['Price'] = data_w_zip_latlon['2022-10-31']
    data_w_zip_latlon = data_w_zip_latlon[['Neighborhood','latlon','zipcode','RegionID','State','City','Metro','Price','bedrooms','Region','State Name']]
    # Load in price forecasts
    price_forecasts = pd.read_csv('data/zillow_data/pricing_forecast.csv')    
    price_forecasts = price_forecasts[['RegionName', '2023-10-31']]
    # Merge price forecasts into project dataset
    complete_df = pd.merge(data_w_zip_latlon, price_forecasts, left_on='zipcode', right_on='RegionName', how='left')
    print(data_w_zip_latlon)
    # Reformat dataset
    complete_df['zipcode'] = complete_df['RegionName']
    complete_df['forecast'] = complete_df['2023-10-31']
    complete_df = complete_df[['Neighborhood','latlon','zipcode','RegionID','State','City','Metro','Price','bedrooms','Region','State Name', 'forecast']]
    complete_df.to_csv('data/project_dataset.csv', index=False)


# Make a query from the frontend
def make_query(args):
    # If the necessary nd has not been generated yet, create it
    if not os.path.exists('data/project_dataset.csv'):
        generate_dataset()
    # Read in the compiled data
    data = pd.read_csv('data/project_dataset.csv').fillna(0)
    # Each of the four following lines filters out results that do not adhere to the inputs
    with_region = data[data['Region'] == args['region']]
    with_bedrooms = with_region[with_region['bedrooms'] == int(args['beds'])]
    bottom_price, top_price = [int(x.strip(' $').replace(',', '')) for x in args['price'].split('-')]
    with_all = with_bedrooms.loc[(with_bedrooms['Price'] >= bottom_price) & (with_bedrooms['Price']  <= top_price)]
    # Get mortgage rate and timeline to calculate monthly payment using numpy_financial
    rate = sum([int(x.strip().replace('%','')[0]) for x in args['rate'].split('-')]) / 2
    timeline = int(args['timeline'].split()[0])
    with_all['monthly_payment'] = with_all['Price'].apply(lambda x: f'${round(-1 * npf.pmt(rate / 100 / 12, 12 * timeline,x), 2):,.2f}')
    print(args['forecast'])
    if not args['forecast']:
        # Get the top 5 most expensive and top 5 least expensive results to display on the frontend
        most_and_least_expensive = pd.concat([with_all.sort_values(by=['Price'], ascending = False).head(), with_all.sort_values(by=['Price']).head()], join='inner', ignore_index=True)
        # Run the geocoding function to get coordinates and return
        most_and_least_expensive['Price'] = most_and_least_expensive['Price'].apply(lambda x: f'${x:,.2f}')
        return most_and_least_expensive
    # Calculate forecasted price changes
    with_all['price_change'] = with_all.apply(lambda x: x['Price'] * x['forecast'] / 100, axis=1)
    ## Get highest and lowest expected price change
    highest_and_lowest_change = pd.concat([with_all.sort_values(by=['price_change'], ascending = False).head(), with_all.sort_values(by=['price_change']).head()], join='inner', ignore_index=True)
    # Format prices for frontend
    highest_and_lowest_change['price_change'] = highest_and_lowest_change['price_change'].apply(lambda x: f'${x:,.2f}')
    highest_and_lowest_change['Price'] = highest_and_lowest_change['Price'].apply(lambda x: f'${x:,.2f}')
    return highest_and_lowest_change

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