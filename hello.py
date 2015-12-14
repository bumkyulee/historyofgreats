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
from flask.ext.cache import Cache

from save_historians import *
import time
import random

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
app.cache = Cache(app, config={
         'CACHE_TYPE': 'filesystem',
         'CACHE_DIR': 'cache-dir',
         'CACHE_DEFAULT_TIMEOUT': 922337203685477580,
         'CACHE_THRESHOLD': 922337203685477580
     })

@app.route("/")
def main():
	return 'nginx is running'

@app.route("/historyofgreats")
def historyofgreats():
	cached = app.cache.get('main')
	if cached:
		return cached
	worksheet = setWorkSheet()
	data = worksheet.get_all_values()
	result = render_template('graphs.html',data=data)
	app.cache.set('main', result)
	return result

@app.route("/claim", methods=["POST"])
def claim():
	claimtype = request.form.get('claimtype')
	msg = request.form.get('msg')
	result = saveClaim(claimtype,msg)
	return json.dumps(result)

@app.route("/add", methods=["POST"])
def add():
	name = request.form.get('name')
	result =  addHistory(name)
	return json.dumps(result)

#Flush Cache
@app.route("/cache_flush/<key_name>")
def cache_flush(key_name):
	app.cache.delete(key_name)
	return 'Done: [ ' + key_name + ' ] is Deleted'

#test
@app.route("/test/<name>")
def test(name):
	result =  getinfoWiki(name)
	return json.dumps(result)

if __name__ == "__main__":
 	app.run('0.0.0.0',8080,debug=True)













