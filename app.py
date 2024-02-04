from flask import Flask, render_template,request
import numpy as np
from joblib import load
from database import engine
from sqlalchemy import text

app = Flask(__name__)

def load_build_parts(pred):
    with engine.connect() as connection:
        build = {
            'case': connection.execute(text("SELECT * FROM cases WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price = pred[0][19]))).fetchone()
        }
        print(build['case']['Title'])
    return build

@app.route("/", methods=['GET', 'POST'])
def index():
    request_type = request.method
    if request_type == 'GET': 
        return render_template("index.html")
    else:
        budget = int(request.form['budget'])
        usage = int(request.form['usage'])
        model = load('regression_model.joblib')
        regression_pred = model.predict(np.array([[usage, budget]]))
        
        build = load_build_parts(regression_pred)

        return render_template("result.html", build=build)

if __name__ == "__main__":
    app.run(debug=True)
