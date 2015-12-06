# coding: utf-8
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import random
from flask import request

from save_historians import *

app = Flask(__name__)

@app.route("/connect")
def connect():
	worksheet = setWorkSheet()
	data = worksheet.get_all_values()

	return render_template('graphs.html',data=data)

@app.route("/claim", methods=["POST"])
def claim():
	claimtype = request.form.get('claimtype')
	msg = request.form.get('msg')
	result = saveClaim(claimtype,msg)
	return json.dumps(result)

# 테스트용
@app.route("/add", methods=["POST"])
def add():
	name = request.form.get('name')
	nationality = request.form.get('nationality')
	result =  addHistory(name,nationality)
	return json.dumps(result)

# 테스트용
@app.route("/test/<name>")
def test(name):
	result = getinfoWiki(name)
	return json.dumps(result)


if __name__ == "__main__":
 	app.run('0.0.0.0',8080,debug=True)













