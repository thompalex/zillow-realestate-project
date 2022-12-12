from flask import Flask, render_template, request
import os
import json
from data_work import make_query

app = Flask(__name__)

# Backend to host our app

# Homepage actually displayed to user
@app.route("/")
def homepage():
    google_api_key = os.getenv('GOOGLE_MAPS_KEY')
    return render_template('form_with_map.html', google_api_key=google_api_key)


# The frontend makes calls to the API route here
# Here, we call functions from the data_work file and return the results
@app.route("/api", methods=["POST"])
def get_suggestion():
    args = request.get_json()
    res = make_query(args).to_dict('records')
    return json.dumps(res)

if __name__ == "__main__":
    app.run(host='0.0.0.0')