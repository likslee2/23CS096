from flask import Flask, render_template,request
import numpy as np
from joblib import load

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    request_type = request.method
    if request_type == 'GET': 
        return render_template("index.html")
    else:
        budget = int(request.form['budget'])
        usage = int(request.form['usage'])
        model = load('web/regression_model.joblib')
        pred = model.predict(np.array([[usage, budget]]))
        return render_template("index.html", result=pred)

if __name__ == "__main__":
    app.run(debug=True)
