from flask import Flask, render_template,request
import numpy as np
from joblib import load
from database import engine
from sqlalchemy import text

app = Flask(__name__)

def features_onehot(budget, usage):
    if usage == "office work": return np.array([[0, 0, 1, budget]])
    elif usage == "gaming": return np.array([[0, 1, 0, budget]])
    elif usage == "editing": return np.array([[1, 0, 0, budget]])
    else: return False

def load_build_parts(regression_pred, classification_pred):
    with engine.connect() as connection:
        build = {
            'cpu': connection.execute(text("SELECT * FROM cpu_dataset WHERE Price <={price:.2f} AND Cores >= {cores} AND Threads >={threads} AND Base speed >= {base_speed} AND Turbo speed >= {turbo_speed} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[0], cores=regression_pred[1], threads=regression_pred[2], base_speed=regression_pred[3], turbo_speed=regression_pred[4]))).fetchone(),
            'cooler': connection.execute(text("SELECT * FROM cooling_dataset WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[5]))).fetchone(),
            'motherboard': connection.execute(text("SELECT * FROM motherboard_dataset WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[6]))).fetchone(),
            'ram': connection.execute(text("SELECT * FROM ram_dataset WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[7]))).fetchone(),
            'storage': connection.execute(text("SELECT * FROM storage_dataset WHERE Price <={price:.2f} AND Type = '{type}' ORDER BY Price DESC LIMIT 1".format(price=regression_pred[15], type=classification_pred[1]))).fetchone(),
            'gpu': connection.execute(text("SELECT * FROM gpu_dataset WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[12]))).fetchone(),
            'psu': connection.execute(text("SELECT * FROM psu_dataset WHERE Price <={price:.2f} AND Efficiency = '{efficiency}' ORDER BY Price DESC LIMIT 1".format(price=regression_pred[17], efficiency=classification_pred[2]))).fetchone(),
            'case': connection.execute(text("SELECT * FROM case_dataset WHERE Price <={price:.2f} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[18]))).fetchone()
        }
    return build


def cal_cost(build):
    cost = 0
    for component in build:
        cost += float(build[component]['Price'])
    return cost

@app.route("/", methods=['GET', 'POST'])
def index():
    request_type = request.method
    if request_type == 'GET': 
        return render_template("index.html")
    else:
        query_features = features_onehot(int(request.form['budget']), request.form['usage'])
        
        regression_model = load('multiple_regression_model.joblib')
        regression_pred = regression_model.predict(query_features)
        classification_model = load('random_forest_classification_model.joblib')
        classification_pred = classification_model.predict(query_features)
        
        build = load_build_parts(regression_pred[0], classification_pred[0])
        cost = cal_cost(build)
        components_info = {
            'ram_size': int(int(build['ram']['Ram size'])/int(build['ram']['Quantity'])),
            'gpu_memory': int(build['gpu']['Memory'])
        }
        
        return render_template("result.html", build=build, cost=cost, components_info=components_info)

if __name__ == "__main__":
    app.run(debug=True)
