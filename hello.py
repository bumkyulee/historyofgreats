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

	return render_template('graphs_clean.html',data=data)

@app.route("/findperiod/<schName>")
def findPeriod(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		url = 'http://terms.naver.com/search.nhn?query='+schName.encode('utf-8')+'&searchType=text&dicType=&subject=1200'
		page = opener.open(url)
	       	soup = BeautifulSoup(page)
	       	infos = soup.findAll('dt')
	       	for info in infos:
	       		if info.find('a').text.find(' ~ ') >= 0:
	       			data = info.find('a').text
	       			break
	       	#data = soup.findAll('dt')[0].find('a').text
	       	birth = data.split(',')[1].split(' ')[1].split('.')[0].encode('utf-8')
	       	death = data.split(',')[1].split(' ')[3].split('.')[0].encode('utf-8')

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
		depth = random.randrange(1,3)
		row = len(data)+1

		#국가는 랜덤으로..
		nationalities = ['Korea','America','Japan','China','France']
		nationality = nationalities[random.randrange(1,len(nationalities))]

		worksheet.update_cell(row, 1, schName)
		worksheet.update_cell(row, 2, birth)
		worksheet.update_cell(row, 3, death)
		worksheet.update_cell(row, 4, nationality)
		worksheet.update_cell(row, 5, depth)

		return '완료 :' + birth + '~' +death + ' / ' + '랜덤하게 ' + nationality + '인이 되었습니다'
	except:
		return '오류가 발생했지만 시간이 부족하여 잡지 못했습니다'

def update_one(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		url = 'http://terms.naver.com/search.nhn?query='+schName.encode('utf-8')+'&searchType=text&dicType=&subject=1200'
		page = opener.open(url)
	       	soup = BeautifulSoup(page)
	       	infos = soup.findAll('dt')
	       	for info in infos:
	       		if info.find('a').text.find(' ~ ') >= 0:
	       			data = info.find('a').text
	       			break
	       	birth = data.split(',')[1].split(' ')[1].split('.')[0].encode('utf-8')
	       	death = data.split(',')[1].split(' ')[3].split('.')[0].encode('utf-8')
		depth = random.randrange(1,3)

		#국가는 랜덤으로..
		nationalities = ['Korea','America','Japan','China','France']
		nationality = nationalities[random.randrange(1,len(nationalities))]
		value = [birth,death,nationality,depth]
		return value
	except:
		value = [0,0,0,0]
		return value

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

@app.route("/getinfo/<schName>")
def getinfo(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		url = 'http://ko.wikipedia.org/wiki/'+schName.encode('utf-8')
		page = opener.open(url)
	       	soup = BeautifulSoup(page)
	       	infobox = soup.find('table').findAll('tr')
	       	birth = 0
	       	death = 0
	       	nationality = ''

	       	birth_strs = ['출생']
	       	death_strs = ['사망']
	       	nationality_strs = ['왕조','국적','출생지']

	       	#getFullName
	       	name = soup.find('h1',attrs={'id':'firstHeading'}).text

	       	#InfoBox parsing
	       	for data in infobox:
	       		label = data.find('th')
	       		if label is not None:
	       			text = label.text.encode('utf-8')
		       		if findString(text,birth_strs) and birth == 0:
		       			birth = data.td.text.split(u'년')[0]
		       		elif findString(text,death_strs) and death == 0:
		       			death = data.td.text.split(u'년')[0]
		       		elif findString(text,nationality_strs) and nationality == '':
		       			nationality = data.td.a is not None and data.td.a.text or '미정'
		       		else:
		       			pass
		value = [birth,death,nationality]
		return json.dumps(value)
	except:
		value = [0,0,'none']
		return json.dumps(value)

def findString(text,strs):
	return any(x in text for x in strs)

@app.route("/findperiod_all")
def findPeriod_all():
	# 다음을 사용하기 전에 발급받은 json키의 client_email로 Spreadsheet를 공유해야 한다.
	SCOPE = ["https://spreadsheets.google.com/feeds"]
	 #json키 저장해서 써야함.
	SECRETS_FILE = "API Project-43d918462212.json"

	json_key = json.load(open(SECRETS_FILE))
	credentials = SignedJwtAssertionCredentials(json_key['client_email'],json_key['private_key'], SCOPE)

	gc = gspread.authorize(credentials)
	sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1MpGW0Hi54_EiIRu-Sx2t1vOgK06p7Hf4ZpWwn4ssHgA/edit')
	worksheet = sht.worksheet("sheet1")
	data = worksheet.get_all_values()

	for i in range(1,len(data)-1):
		schName = data[i][0]
		value = update_one(schName)
		worksheet.update_cell(i+1, 2, value[0])
		worksheet.update_cell(i+1, 3, value[1])
		worksheet.update_cell(i+1, 4, value[2])
		worksheet.update_cell(i+1, 5, value[3])

	return 'ok'

if __name__ == "__main__":
 	app.run('0.0.0.0',8080,debug=True)
