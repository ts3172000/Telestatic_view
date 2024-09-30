import joblib
import numpy as np
from flask import Flask, request, jsonify, render_template,send_file
import pandas as pd
import random
import sqlite3
from sqlite3 import Error
import seaborn as sns
import os
from plots import multi_plots as plot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
from lime_report.lime_plot import lime_plot
from lime_report.lime_prob_plot import prob_lime_plot 
from flask import Flask, url_for, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from recommend.recommend_suggest import recommendations_fun
from uploads.file_upload_prediction import file_upload_pred

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Load saved models
ml_model = joblib.load('models/nate_random_forest.sav')

# Dictionary of all loaded models
loaded_models = {
    'knn': ml_model
}

# recommendations_list
recommendations_list = ["Enhanced Customer Support", "Personalized Services", "Flexible Plans", " Network Quality", "Referral Programs", "Technological Advancements", "Data Protection", "Fraud Prevention", "R&D Investment",
                         "r10"]

# db func start
database = r"./db/sqlite1.db"


# -----------------------File upload and predion------------------

# Creating the upload folder
upload_folder = "uploads/"
if not os.path.exists(upload_folder):
   os.mkdir(upload_folder)

# Configuring the upload folder
app.config['UPLOAD_FOLDER'] = upload_folder

# configuring the allowed extensions
allowed_extensions = ['csv']

def check_file_extension(filename):
    print(filename.split('.')[-1])
    return filename.split('.')[-1] in allowed_extensions

@app.route('/upload', methods = ['GET', 'POST'])
def uploadfile():
    if session.get('logged_in'):

        if request.method == 'POST': # check if the method is post
            files = request.files.getlist('files') # get the file from the files object
            print(files)
            for f in files:
                print(f.filename)
                # Saving the file in the required destination
                if check_file_extension(f.filename) == True:
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'] ,secure_filename(f.filename))) # this will secure the file
                    msg = 'file uploaded successfully....!'
                    file_name = f.filename
                    file_upload_pred(file_name, recommendations_list, ml_model)
                else:
                    msg = "The file extension is not allowed"
            return render_template("predict.html", upload_succes_msg=msg )# Display thsi message after uploading
    else:
        return render_template('login.html')

# Sending the file to the user
@app.route('/download')
def download():
    if session.get('logged_in'):
        print("====================================")
        return send_file('./uploads/predicted_file.csv', as_attachment=True)
    else:
        return render_template('login.html')

# ----------------------------------------------------------------
# ------------------user login and sin-up ------------------------


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password

#home page route
@app.route('/', methods=['GET'])
def index():
    if session.get('logged_in'):
        return render_template('index.html')
    else:
        return render_template('login.html')
    
#home page route
@app.route('/credits', methods=['GET'])
def credits():
    if session.get('logged_in'):
        return render_template('credits.html')
    else:
        return render_template('credits.html')

#register page route
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db.session.add(User(username=request.form['username'], password=request.form['password']))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('register.html', message=f"User {request.form['username']} Already Exists. Please try to login")
    else:
        return render_template('register.html')

#login page route
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', message="login details incorrect. please try again")

#logout page route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))



# ------------------------------------------
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("conn done")
    except Error as e:
        print(f"error is {e}")

    return conn


def create_project(conn, project):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    sql = ''' INSERT INTO df_pred_info(c_id,complains,charge_amount,seconds_of_use,frequency_of_use,frequency_of_sms,age_group,customer_value,Exited,recommendations_1,recommendations_2)
              VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, project)
    conn.commit()
    return cur.lastrowid

# db func end 


# # Function to decode predictions
def decode(pred):
    if pred == 1: return 'Exit'
    else: return 'Stay'

# # Function to decode Gender
# def Gender_invers(Gender):
#     if Gender == "0":
#         return "Female"
#     else:
#         return "Male"
    
# # Function to decode Geography
# def Geography_invers(Geography):
#     if Geography == "0":
#         return "France"
#     elif Geography == "1":
#         return "Spain"
#     elif Geography == "2":
#         return"Germany"
    

@app.route('/')
def home():
    if session.get('logged_in'):
        first = request.args.get('first')
        return render_template('index.html', first=first)
    else:
        return render_template('login.html')

@app.route('/about')
def about():
    if session.get('logged_in'):
        return render_template('about.html')
    else:
        return render_template('login.html')

@app.route('/pred')
def pred():
    if session.get('logged_in'):
        return render_template('predict.html')
    else:
        return render_template('login.html')

@app.route("/getimage")
def get_img():
    if session.get('logged_in'):
        return "/static/img/2.jpg"
    else:
        return render_template('login.html')

# @app.route('/plots')
@app.route('/multivariate_graph') 
def table():
    if session.get('logged_in'):
        con = create_connection(database)
        df = pd.read_sql_query("SELECT * from df_pred_info", con)
        df = df.tail(10)
        return render_template('plots.html', tables=[df.to_html()], titles=[''])
    else:
        return render_template('login.html')

@app.route('/multivariate_graph', methods=['POST'])
# def multivariate_graph(df, graph_name, col_1=None, col_2=None):
def multivariate_graph():
    if session.get('logged_in'):
        values = [x for x in request.form.values()]
        print(values)
        con = create_connection(database)
        df = pd.read_sql_query("SELECT * from df_pred_info", con)
        graph_name = values[0]
        col_1 = values[1]
        col_2 = values[2]
        try:
            if graph_name == "scatterplot":
                if os.path.exists("./static/img/plot_imgs/scatterplot.jpeg"):
                    os.remove("./static/img/plot_imgs/scatterplot.jpeg")
                    plot.scatterplot(df, col_1, col_2)
                else:
                    plot.scatterplot(df, col_1, col_2)

            else:
                if os.path.exists("./static/img/plot_imgs/lineplot.jpeg"):
                    os.remove("./static/img/plot_imgs/lineplot.jpeg")
                    plot.lineplot(df, col_1, col_2)
                else:
                    plot.lineplot(df, col_1, col_2)
        except Exception as e:
            print(e)

        return render_template('plots.html', fig_m=f'../static/img/plot_imgs/{graph_name}.jpeg',
                            tables=[df.tail(10).to_html()], titles=[''])
    else:
        return render_template('login.html')

@app.route('/univariate_graph', methods=['POST'])
def univariate_graph():
    if session.get('logged_in'):
        values = [x for x in request.form.values()]
        print(values)
        con = create_connection(database)
        df = pd.read_sql_query("SELECT * from df_pred_info", con)
        graph_name = values[0]
        col_1 = values[1]
        try:

            if graph_name == "histogram":
                if os.path.exists("./static/img/plot_imgs/histogram.jpeg"):
                    os.remove("./static/img/plot_imgs/histogram.jpeg")
                    # time.sleep(10)
                    plot.histplot(df, col_1)
                else:
                    # time.sleep(10)
                    plot.histplot(df, col_1)

            else:
                if os.path.exists("./static/img/plot_imgs/boxplot.jpeg"):
                    os.remove("./static/img/plot_imgs/boxplot.jpeg")
                    # time.sleep(10)

                    plot.boxplot(df, col_1)
                else:
                    # time.sleep(10)
                    plot.boxplot(df, col_1)

        except Exception as e:
            print(e)

        return render_template('plots.html', fig_u=f'../static/img/plot_imgs/{graph_name}.jpeg',
                            tables=[df.tail(10).to_html()], titles=[''])
    else:
        return render_template('login.html')

@app.route('/predict', methods=['POST'])
def predict():
    if session.get('logged_in'):
        # List values received from index
        values = [x for x in request.form.values()]
        c_ids = values[0]
        values = values
        new_array = np.array(values).reshape(1, -1)
        print("----------", new_array)
        print("+++++++++", values)
        # Key names for customer dictionary custd
        cols = ['complains',
                'charge_amount',
                'seconds_of_use',
                'frequency_of_use',
                'frequency_of_sms',
                'age_group',
                'customer_value']

        # Create customer dictionary
        custd = {}
        for k, v in zip(cols, values):
            custd[k] = v
        print(custd)

        # Create customer dictionary for lime report 
        custd_lime = {}
        for k, v in zip(cols, values):
            custd_lime[k] = [int(v)]
        df_for_pred_view = pd.DataFrame(custd_lime)
        # loaded_models__=loaded_models['knn']
        print(f"++++++++++custd_lime+++++++++{custd_lime}")

        prob_lime_path = prob_lime_plot(custd_lime)    
        
        lime_plot_file_path = lime_plot(custd_lime)    
        # prob_lime_path = prob_lime_plot(custd_lime)    

        # save predictiond to the list
        predl = []
        for m in loaded_models.values():
            predl.append(decode(m.predict(new_array)[0]))
        if predl[0] == "Exit":
            r1, r2 = recommendations_fun(recommendations_list)
            recommendations = "Recommendations"
            recod_1 = r1
            recod_2 = r2
        else:
            recommendations = " "
            recod_1 = " "
            recod_2 = " "

        # db start 
        c_id = int(c_ids)
        complains = custd['complains']
        charge_amount = custd['charge_amount']
        seconds_of_use = custd['seconds_of_use']
        frequency_of_use = custd['frequency_of_use']
        frequency_of_sms = custd['frequency_of_sms']
        age_group = custd['age_group']
        customer_value = custd['customer_value']
        pred = predl[0]
        recommendations_1 = recod_1
        recommendations_2 = recod_2

        conn = create_connection(database)
        project = (c_id, complains, charge_amount, seconds_of_use, 
                frequency_of_use, frequency_of_sms, age_group, customer_value, 
                pred, recommendations_1, recommendations_2);
        create_project(conn, project)

        # db end 

        shape_img = "/static/img/2.jpg"

        return render_template("predict.html",
                            pred_out=f"This customer will {predl[0]} \
                            in your branch",
                            recommendations=recommendations,
                            recod_1=recod_1, recod_2=recod_2,
                            shape_img=shape_img,
                            lime_info=lime_plot_file_path,
                            prob_lime=prob_lime_path,
                            tables=[df_for_pred_view.tail(10).to_html()],
                            titles=[''])
    else:
        return render_template('login.html')

if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8080)
    # app.run(debug=True)
    app.secret_key = "ThisIsNotASecret:p"
    with app.app_context():
        app.secret_key = "ThisIsNotASecret:p"

        db.create_all()
        app.run(debug=True,port=8080)
