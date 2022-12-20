from flask import Flask, render_template, request
import os
import json
from data_work import make_query
from search import Limit
import yaml
from dotenv import load_dotenv

app = Flask(__name__, 
            static_folder='./static', 
            template_folder='./templates',
            )

# Backend to host our app

# Homepage actually displayed to user
@app.route("/")
def homepage():
    load_dotenv()
    google_api_key = os.getenv('GOOGLE_MAPS_KEY')
    parameter = open('config_param.yml', 'rb')
    parameter = yaml.safe_load(parameter)
    queryLimit = Limit(**parameter)
    return render_template('form_with_map.html', google_api_key=google_api_key, parameter = queryLimit.param())


# The frontend makes calls to the API route here
# Here, we call functions from the data_work file and return the results
@app.route("/api", methods=["POST"])
def get_suggestion():
    args = request.get_json()
    tables, dfs, errorLog = make_query(args)
    if tables is None:
        return errorLog
    return json.dumps({"tables": tables, "dfs": dfs})

if __name__ == "__main__":
    app.run(host='0.0.0.0')
