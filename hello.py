# coding: utf-8
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

app = Flask(__name__)

@app.route("/")
def hello():
    	return "apache is running ok?"

@app.route("/connect")
def connect():
	# 다음을 사용하기 전에 발급받은 json키의 client_email로 Spreadsheet를 공유해야 한다.
	SCOPE = ["https://spreadsheets.google.com/feeds"]
	 #json키 저장해서 써야함.
	SECRETS_FILE = "API Project-43d918462212.json"

	json_key = json.load(open(SECRETS_FILE))
	credentials = SignedJwtAssertionCredentials(json_key['client_email'],json_key['private_key'], SCOPE)

	gc = gspread.authorize(credentials)
	#sht  = gc.open("historyofgreats")
	sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1MpGW0Hi54_EiIRu-Sx2t1vOgK06p7Hf4ZpWwn4ssHgA/edit')
	worksheet = sht.worksheet("sheet1")
	data = worksheet.get_all_values()

	return render_template('graphs.html',data=data)

@app.route("/test")
def test():
	return findPeriod('')

def findPeriod(schName):
	return 'nothing'

if __name__ == "__main__":
 	app.run('0.0.0.0',8080,debug=True)
