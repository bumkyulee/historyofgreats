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


app = Flask(__name__)

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

@app.route("/add")
def add():
	return render_template('add.html')

@app.route("/claim")
def claim():
	return '작업중입니다'

@app.route("/add/item")
def add_item():
	return '1'

# 테스트 용으로 잠시 놔둠
@app.route("/getinfobing/<schName>")
def getinfobing(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		url = u'http://www.bing.com/search?q='+schName
		url = urllib.quote(url.encode('utf8'), '/:')
		page = opener.open(url)
	       	soup = BeautifulSoup(page)
		name = soup.findAll('h2',attrs={'class':' b_entityTitle'})[0].text
		infobox = soup.find('ul',attrs={'class':'b_vList'}).findAll('li')

	       	birth_strs = ['출생:']
	       	death_strs = ['사망:']
	       	birth = '?'
	       	death = '?'

		for data in infobox:
	   		text = data.text.encode('utf-8')
	   		temp = text.replace('AD ','').replace(':',' ').replace('년',' ').split(' ')[1]
	   		if findString(temp,'BC '):
	   			 raise Exception('BC')
	       		if findString(text,birth_strs):
	       			birth = temp
	       		elif findString(text,death_strs):
	       			death = temp
	       		else:
	       			pass
	       	value = [name,birth,death]
	except Exception, e:
		value = [0,0,e.args[0]]
       	return json.dumps(value)

if __name__ == "__main__":
 	app.run('0.0.0.0',8080,debug=True)
