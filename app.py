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
            'cpu': connection.execute(text("SELECT * FROM cpu_dataset WHERE Price <= {price:.2f} AND Cores <= {cores} AND Threads <= {threads} AND 'Base Speed' <= {base_speed} AND 'Turbo Speed' <= {turbo_speed} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[0], cores=regression_pred[1], threads=regression_pred[2], base_speed=regression_pred[3], turbo_speed=regression_pred[4]))).fetchone(),
            'cooler': connection.execute(text("SELECT * FROM cooling_dataset WHERE Price <= {price:.2f} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[5]))).fetchone(),
            'motherboard': connection.execute(text("SELECT * FROM motherboard_dataset WHERE Price <= {price:.2f} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[6]))).fetchone(),
            'ram': connection.execute(text("SELECT * FROM ram_dataset WHERE Price <= {price:.2f} AND 'Ram size' <= {size} AND Quantity <= {quantity} AND 'Ram speed' <= {speed} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[7], size=regression_pred[8], quantity=round(regression_pred[9], 1), speed=regression_pred[10]))).fetchone(),
            # 'ram': connection.execute(text("SELECT * FROM ram_dataset WHERE Price <= {price:.2f} AND 'Ram size' <= {size} AND Quantity <= {quantity} AND 'Ram speed' <= {speed} AND 'CAS latency' >= {cl} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[7], size=regression_pred[8], quantity=round(regression_pred[9], 1), speed=regression_pred[10], cl=regression_pred[11]))).fetchone(),

            'storage': connection.execute(text("SELECT * FROM storage_dataset WHERE Price <= {price:.2f} AND Type = '{type}' ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[15], type=classification_pred[1]))).fetchone(),
            'gpu': connection.execute(text("SELECT * FROM gpu_dataset WHERE Price <= {price:.2f} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[12]))).fetchone(),
            'psu': connection.execute(text("SELECT * FROM psu_dataset WHERE Price <= {price:.2f} AND Efficiency = '{efficiency}' ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[17], efficiency=classification_pred[2]))).fetchone(),
            'case': connection.execute(text("SELECT * FROM case_dataset WHERE Price <= {price:.2f} ORDER BY Price DESC LIMIT 1;".format(price=regression_pred[18]))).fetchone()
        }
        print(text("SELECT * FROM ram_dataset WHERE Price <={price:.2f} AND 'Ram size' <= {size} AND Quantity <= {quantity} AND 'Ram speed' <= {speed} AND 'CAS latency' >= {cl} ORDER BY Price DESC LIMIT 1".format(price=regression_pred[7], size=regression_pred[8], quantity=int(regression_pred[9]), speed=regression_pred[10], cl=regression_pred[11])))
        for i in build:
            print(build[i])
    return build


def cal_cost(build):
    cost = 0
    for component in build:
        cost += float(build[component]['Price'])
    return round(cost, 2)

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
