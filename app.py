from flask import Flask, render_template,request
import numpy as np
from joblib import load
from database import engine
from sqlalchemy import text
from forex_python.converter import CurrencyRates

app = Flask(__name__)
cr = CurrencyRates()
hkd_to_usd = cr.get_rate('HKD', 'USD')
usd_to_hkd = cr.get_rate('USD', 'HKD')

def features_onehot(budget, usage):
    if usage == "office work": return np.array([[0, 0, 1, budget]])
    elif usage == "gaming": return np.array([[0, 1, 0, budget]])
    elif usage == "editing": return np.array([[1, 0, 0, budget]])
    else: return False

def find_cpu(price, cores, threads, base_speed, turbo_speed):
    cpu = None
    while cpu == None:
        cpu = engine.connect().execute(text("SELECT *, SQRT(POW((Cores - {cores}), 2) + POW(({threads} - 20), 2) + POW((Base_Speed - {base_speed}), 2) + POW((Turbo_Speed -  {turbo_speed}), 2)) AS distance FROM cpus WHERE Price <= {price:.2f} ORDER BY distance LIMIT 1;".format(price=price, cores=cores, threads=threads, base_speed=base_speed, turbo_speed=turbo_speed))).fetchone()
        if cpu == None: price+=13
    return cpu

def find_cooler(price):
    cooler = None
    while cooler == None:
        cooler = engine.connect().execute(text("SELECT * FROM coolers WHERE Price <= {price:.2f} ORDER BY price DESC LIMIT 1;".format(price=price))).fetchone()
        if cooler == None: price+=13
    return cooler

def find_motherboard(type, price):
    motherboard = None
    while motherboard == None:
        motherboard = engine.connect().execute(text("SELECT * FROM motherboards WHERE Socket_type = '{type}' AND Price <= {price:.2f} ORDER BY price DESC LIMIT 1;".format(type=type, price=price))).fetchone()
        if motherboard == None: price+=13
    return motherboard

def find_ram(standard, price, size, quantity, speed, cl):
    ram = None
    while ram == None:
        ram = engine.connect().execute(text("SELECT *, SQRT(POW((Ram_size - {size}), 2) + POW((Ram_speed - {speed}), 2) + POW((CAS_latency -  {cl}), 2)) AS distance FROM rams WHERE Price <= {price:.2f} AND Ram_standard = '{standard}' AND Quantity <= {quantity} ORDER BY distance LIMIT 1;".format(standard=standard, price=price, size=size, quantity=quantity, speed=speed, cl=cl))).fetchone()
        if ram == None: price+=13
    return ram

def find_storage(capacity, price, type):
    storage = None
    while storage == None:
        storage = engine.connect().execute(text("SELECT *, SQRT(POW((Capacity - {capacity}), 2)) AS distance FROM storages WHERE Price <= {price:.2f} AND Type = '{type}' ORDER BY distance ASC, Price DESC LIMIT 1;".format(capacity=capacity, price=price, type=type))).fetchone()
        if storage == None: price+=13
    return storage

def find_gpu(speed, memory, price):
    gpu = None
    while gpu == None:
        gpu = engine.connect().execute(text("SELECT *, SQRT(POW((Base_clock - {speed}), 2) + POW((Memory - {memory}), 2)) AS distance FROM gpus WHERE Price <= {price:.2f} ORDER BY Price DESC LIMIT 1;".format(speed=speed, memory=memory, price=price))).fetchone()
        if gpu == None: price+=13
    return gpu

def find_psu(price, efficiency):
    psu = None
    while psu == None:
        psu = engine.connect().execute(text("SELECT * FROM psus WHERE Price <= {price:.2f} AND Efficiency = '{efficiency}' ORDER BY price DESC LIMIT 1;".format(price=price, efficiency=efficiency))).fetchone()
        if psu == None: price+=13
    return psu

def find_case(cabinet_type, price):
    case = None
    while case == None:
        case = engine.connect().execute(text("SELECT * FROM cases WHERE Cabinet_type LIKE '{cabinet_type}' AND Price <= {price:.2f} ORDER BY price DESC LIMIT 1;".format(cabinet_type=cabinet_type, price=price))).fetchone()
        if case == None: price+=13
    return case



def load_build_parts(pred):
    cpu = find_cpu(pred["cpu"]["price"], pred["cpu"]["price"], pred["cpu"]["price"], pred["cpu"]["base_speed"], pred["cpu"]["turbo_speed"])
    
    if (pred["cooler"]["type"] != "None"):
        cooler = find_cooler(pred["cooler"]["price"])
    
    motherboard = find_motherboard(cpu["Socket Type"], pred["motherboard"]["price"])
    
    ram1 = find_ram(cpu["Memory Generation"], pred["ram1"]["price"], pred["ram1"]["size"], round(pred["ram1"]["quantity"], 1), pred["ram1"]["speed"], pred["ram1"]["cl"])
    
    if (pred["ram2"]["quantity"] >= 1):
        ram2 = find_ram(cpu["Memory Generation"], pred["ram2"]["price"], pred["ram2"]["size"], round(pred["ram2"]["quantity"], 1), pred["ram2"]["speed"], pred["ram2"]["cl"])
    else:
        ram2 = None
    
    storage = find_storage(pred["storage"]["capacity"], pred["storage"]["price"], pred["storage"]["type"])
    
    gpu = find_gpu(pred["gpu"]["speed"], pred["gpu"]["memory"], pred["gpu"]["price"])
    
    psu = find_psu(pred["psu"]["price"], pred["psu"]["efficiency"])
    
    if (motherboard["Form factor"] == "ATX" or motherboard["Form factor"] == "Extended ATX"): 
        cabinet_type = "ATX%"
    elif motherboard["Form factor"] == "Mirco ATX":
        cabinet_type = "MircoATX%"
    else:
        cabinet_type = "Mini ITX"
    case = find_case(cabinet_type, pred["case"]["price"])

    build = {
        'cpu': cpu,
        'cooler': cooler,
        'motherboard': motherboard,
        'ram1': ram1,
        'ram2': ram2,
        'storage': storage,
        'gpu': gpu,
        'psu': psu,
        'case': case
    }

    print("Result Build: ")
    for i in build:
        print(build[i])
    return build

def cal_total_cost(build):
    total_cost = 0
    for component in build:
        if build[component] != None: total_cost += float(build[component]['Price'])
    return round(total_cost*usd_to_hkd, 2)

@app.route("/", methods=['GET', 'POST'])
def index():
    request_type = request.method
    if request_type == 'GET': 
        return render_template("index.html", build=None)
    else:
        budget = int(request.form['budget'])*hkd_to_usd
        usage = request.form['usage']
        print("Budget: {b}\nUsage: {u}".format(b=int(request.form['budget']), u=usage))
        query_features = features_onehot(budget, usage)
        
        regression_model = load('multiple_regression_model.joblib')
        regression_pred = regression_model.predict(query_features)[0]
        classification_model = load('knn_classification_model.joblib')
        classification_pred = classification_model.predict(query_features)[0]
        
        pred = {
            "cpu" : {
                "price" : regression_pred[0],
                "cores" : regression_pred[1],
                "threads" : regression_pred[2],
                "base_speed" : regression_pred[3],
                "turbo_speed" : regression_pred[4],
            },
            "cooler" : {
                "price" : regression_pred[5],
                "type" : classification_pred[0]
            },
            "motherboard" : {
                "price" : regression_pred[6]
            },
            "ram1" : {
                "price" : regression_pred[7],
                "size" : regression_pred[8],
                "quantity" : regression_pred[9],
                "speed" : regression_pred[10],
                "cl" : regression_pred[11],
                "standard" : classification_pred[1]
            },
            "ram2" : {
                "price" : regression_pred[12],
                "size" : regression_pred[13],
                "quantity" : regression_pred[14],
                "speed" : regression_pred[15],
                "cl" : regression_pred[16],
                "standard" : classification_pred[2]
            },
            "gpu" : {
                "price" : regression_pred[17],
                "speed" : regression_pred[18],
                "memory" : regression_pred[19]
            },
            "storage" : {
                "price" : regression_pred[20],
                "capacity" : regression_pred[21],
                "type" : classification_pred[3]
            },
            "psu" : {
                "price" : regression_pred[22],
                "efficiency" : classification_pred[4]
            },
            "case" : {
                "price" : regression_pred[23],
            }
        }
        print("Prediction: ")
        for i in pred:
            print(i, pred[i])
        print('\n')
        
        build = load_build_parts(pred)
        total_cost = cal_total_cost(build)
        components_info = {
            'ram1_size': int(int(build['ram1']['Ram_size'])/int(build['ram1']['Quantity'])),
            'gpu_memory': int(build['gpu']['Memory'])
        }

        converted_price=[]
        for component in build:
            if (build[component] == None):
                converted_price.append(0)
                continue
            converted_price.append(round(build[component]['Price']*usd_to_hkd, 2))
        
        return render_template("index.html", build=build, total_cost=total_cost, components_info=components_info, scroll_id='result', converted_price=converted_price)

if __name__ == "__main__":
    app.run(debug=True)
