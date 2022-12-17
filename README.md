# Zillow Real Estate Project By Alex Thompson, Rohil Navani, and Hailey Nguyen

If you wish to run our project, first create a .env file in the project directory with a google maps api key and two positionstack api keys as follows:

POSITIONSTACK_KEY1='<positionstack_api_key1>'

POSITIONSTACK_KEY2='<positionstack_api_key2>'

GOOGLE_MAPS_KEY='<google_maps_api_key>'

Then, create a new virtual environment and enter it with the following commands:

python -m venv venv

source venv/Scripts/activate

Now you can install all of our requirements with

pip install -r requirements.txt

Finally, run the app with

python data_app.py

Now our application should be running locally on localhost:5000!

If you wish to see a more detailed project description, then see project_description.doc
