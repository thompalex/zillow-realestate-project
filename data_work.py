import pandas as pd
import numpy_financial as npf
import http.client, urllib.parse
import json
import os

# This is where the actual data stuff is done for the most part
# Get the longitude/latitude of a given neighborhood with positionstack api
def add_geocoding(data):
    conn = http.client.HTTPConnection('api.positionstack.com')
    # Function to get individual lon/lat
    def get_geocode(neighborhood, city,  state):
        params = urllib.parse.urlencode({
            'access_key': '3e6e9d79072006e5502b0ca27ec0a5bf',
            'query': f'{neighborhood}, {city}, {state}, USA' ,
            'limit': 1,
        })
        conn.request('GET', '/v1/forward?{}'.format(params))
        res = conn.getresponse()
        api_result = json.loads(res.read().decode('utf-8'))
        if 'data' in api_result and api_result['data'][0] != []:
            return f'{api_result["data"][0]["latitude"]}, {api_result["data"][0]["longitude"]}'
        else:
            return ""
    # Create latlon col in the dataframe to be returned to the frontend
    data['latlon'] = data.apply(lambda x: get_geocode(x['RegionName'], x['City'], x['State Name']), axis=1)
    return data


# Generate the project nd from the zillow files and the region mapping
def generate_dataset():
    region_mapping = pd.read_csv('states.csv')
    # Concatenate each of the csvs that correspond to individual bedroom amounts
    arr = []
    for i in range(1, 6):
        nd = pd.read_csv(f'zillow_data/{i}_bedroom.csv')
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
    # Open Neighborhood to latlon and zipcode mapping file
    zip_latlon_mapping = pd.read_csv('unique_neighborhoods_w_zip_latlon.csv')
    # Merge zipcodes and latlons with zillow data
    data_w_zip_latlon = pd.merge(zip_latlon_mapping, data_with_region, left_on=['Neighborhood', 'State', 'City'], right_on=['RegionName', 'State Name', 'City'])
    # Format data nicely
    data_w_zip_latlon['State'] = data_w_zip_latlon['State_y']
    data_w_zip_latlon['Price'] = data_w_zip_latlon['2022-10-31']
    data_w_zip_latlon = data_w_zip_latlon[['Neighborhood','latlon','zipcode','RegionID','State','City','Metro','Price','bedrooms','Region','State Name']]
    # Load in price forecasts
    price_forecasts = pd.read_csv('zillow_data/pricing_forecast.csv')    
    price_forecasts = price_forecasts[['RegionName', '2023-10-31']]
    # Merge price forecasts into project dataset
    complete_df = pd.merge(data_w_zip_latlon, price_forecasts, left_on='zipcode', right_on='RegionName', how='left')
    print(data_w_zip_latlon)
    # Reformat dataset
    complete_df['zipcode'] = complete_df['RegionName']
    complete_df['forecast'] = complete_df['2023-10-31']
    complete_df = complete_df[['Neighborhood','latlon','zipcode','RegionID','State','City','Metro','Price','bedrooms','Region','State Name', 'forecast']]
    complete_df.to_csv('project_dataset.csv', index=False)


# Make a query from the frontend
def make_query(args):
    # If the necessary nd has not been generated yet, create it
    if not os.path.exists('project_dataset.csv'):
        generate_dataset()
    # Read in the compiled data
    data = pd.read_csv('project_dataset.csv')
    # Each of the four following lines filters out results that do not adhere to the inputs
    with_region = data[data['Region'] == args['region']]
    with_bedrooms = with_region[with_region['bedrooms'] == int(args['beds'])]
    bottom_price, top_price = [int(x.strip(' $').replace(',', '')) for x in args['price'].split('-')]
    with_all = with_bedrooms.loc[(with_bedrooms['Price'] >= bottom_price) & (with_bedrooms['Price']  <= top_price)]
    # Get mortgage rate and timeline to calculate monthly payment using numpy_financial
    rate = sum([int(x.strip().replace('%','')[0]) for x in args['rate'].split('-')]) / 2
    timeline = int(args['timeline'].split()[0])
    with_all['monthly_payment'] = with_all['Price'].apply(lambda x: f'${round(-1 * npf.pmt(rate / 100 / 12, 12 * timeline,x), 2):,.2f}')
    # Get the top 5 most expensive and top 5 least expensive results to display on the frontend
    most_and_least_expensive = pd.concat([with_all.sort_values(by=['Price'], ascending = False).head(), with_all.sort_values(by=['Price']).head()], join='inner', ignore_index=True)
    # Run the geocoding function to get coordinates and return
    most_and_least_expensive['Price'] = most_and_least_expensive['Price'].apply(lambda x: f'${x:,.2f}')
    return most_and_least_expensive

### Test statements for these methods ###
if __name__ == '__main__':
    generate_dataset() if not os.path.exists('project_dataset.csv') else None
    result = make_query({
            'region': 'Northeast',
            'beds': "1",
            'price': '800,000 - $1,000,000',
            'rate': '4% - 5%',
            'timeline': '30 years'
        })

    print(result)