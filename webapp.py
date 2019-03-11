from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from flask_mail import Mail, Message

import pprint
import os
import json
import datetime as dt

app = Flask(__name__)

app.debug = True #Change this to False for production

# val = "First line\nNext line"

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'jatrimble777@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/', methods=["GET","POST"])
def home():
    session["current_data"] = {}

    return render_template("home.html", page_title="Home")

@app.route('/dataEntry-<int:num>', methods=["GET","POST"])
def dataEntry(num):
    if num == 1:
        entry1 = {'name':"Your Name", 'key':"submitter_name", 'fail':"Please provide your name"}
        entry2 = {'name':"Entry ID (One word)", 'key':"entry_id", "pretext":"#", "rules":'pattern=\\S+', "fail":"Provide an ID with no whitespace"}
        entry3 = {'name':"Date/Time", 'key':"timestamp", 'autoVal':dt.datetime.now().strftime("%m/%d %H:%M:%S"), "rules":'readonly'}

        btnChoices = [{'link':'2', 'name':"Enter Field Data"}, {'link':'4', 'name':"Enter Lab Data"}]

        return render_template("dataEntry.html", page_title="Basic Data", data_type="Basic Data", page_n=1, requiredData=[entry1,entry2,entry3], choices=btnChoices)

    elif num == 2:
        entry1 = {'name':"Sample Location", 'key':"loc", 'fail':"Please provide the sample location"}
        entry2 = {'name':"Water Temperature", 'key':"temp", "posttext":"ºC", "typef":"number", "rules":"min=0 max=100", 'fail':"Please provide a numeric temperature value between 0 and 100 ºC"}
        entry3 = {'name':"Water pH", 'key':"ph", "typef":"number", "rules":"min=0 max=14", 'fail':"Please provide a numeric pH value between 0 and 14 "}
        entry4 = {'name':"Water Turbulence", 'key':"turbulence", "type":"dropdown", "choices":["Very High", "High", "Medium", "Low", "None/Still"], 'fail':"Please select a turbulence level"}

        return render_template("dataEntry.html", page_title="Field Data", data_type="Field Data", page_n=2, requiredData=[entry1,entry2,entry3, entry4], last_form=True)

    elif num == 4:
        entry1 = {'name':"Concentration of Dissolved Oxygen ([DO])", 'key':"do", "posttext":"g/L", 'typef':"number", "rules":"step=any", "fail":"Please enter the calculated numeric value for the [DO]"}

        return render_template("dataEntry.html", page_title="Lab Data", data_type="Lab Data", page_n=4, requiredData=[entry1], last_form=True)

@app.route('/addData-<int:next>', methods=["GET","POST"])
def addData(next):
    source = int(request.form['last_page'])

    if source == 1:
        oldData = session["current_data"]
        oldData["basic_data"] = dict(request.form)
        session["current_data"] = oldData
        print("Added basic data to cookie")
        # print(session["current_data"])
        return redirect(url_for("dataEntry", num=next))
    elif source == 2:
        oldData = session["current_data"]
        oldData["field_data"] = dict(request.form)
        session["current_data"] = oldData
        # print(session["current_data"])
        return redirect(url_for("submitData"))
    elif source == 4:
        oldData = session["current_data"]
        oldData["lab_data"] = dict(request.form)
        session["current_data"] = oldData
        return redirect(url_for("submitData"))



@app.route('/submitData', methods=["GET","POST"])
def submitData():
    # print(session["current_data"])
    sendData(session["current_data"])

    return redirect(url_for("home")+"?reset=true")

def sendData(inp):
    headerLine = ""
    headerLine += "entryID,submitter,timestamp"
    if "field_data" in inp:
        headerLine += ",location,temperature,pH,turbulence"
    else:
        headerLine += ",[DO]"

    valueLine = "\"%s\",\"%s\",\"%s\"" % (inp['basic_data']['entry_id'], inp['basic_data']['submitter_name'], inp['basic_data']['timestamp'])
    if "field_data" in inp:
        valueLine += ",\"%s\",%s,%s,\"%s\"" % (inp['field_data']['loc'], inp['field_data']['temp'], inp['field_data']['ph'], inp['field_data']['turbulence'])
    else:
        valueLine += ",%s" % inp['lab_data']['do']

    fileBody = "%s\n%s" % (headerLine, valueLine)

    msg = Message('Water Sample (%s)' % dt.datetime.now().strftime("%m/%d %H:%M:%S"), sender = 'jatrimble777@gmail.com', recipients = ['jatrimble777@gmail.com'])

    msg.body = "#######"
    msg.attach("SampleData-%s.csv" % dt.datetime.now().strftime("%m/%d %H:%M:%S"), "text/csv", fileBody)

    mail.send(msg)


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=2050)
