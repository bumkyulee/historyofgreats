# coding: utf-8
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

import urllib2
from BeautifulSoup import BeautifulSoup
import random

def getSoup(url):
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0')]
	page = opener.open(url)
       	soup = BeautifulSoup(page)
       	return soup

def setWorkSheet():
	global worksheet

	#다음을 사용하기 전에 발급받은 json키의 client_email로 Spreadsheet를 공유해야 한다.
	SCOPE = ["https://spreadsheets.google.com/feeds"]
	#json키 저장해서 써야함.
	SECRETS_FILE = "API Project-43d918462212.json"

	json_key = json.load(open(SECRETS_FILE))
	credentials = SignedJwtAssertionCredentials(json_key['client_email'],json_key['private_key'], SCOPE)

	gc = gspread.authorize(credentials)
	#sht  = gc.open("historyofgreats")
	sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1MpGW0Hi54_EiIRu-Sx2t1vOgK06p7Hf4ZpWwn4ssHgA/edit')
	worksheet = sht.worksheet("sheet1")
	print 'done: setWorkSheet'

# 열 단위로 업데이트한다. 열 이름: A,B,C,D,E
def setColumn(col,values,name):
	setWorkSheet()

	if not isinstance(values,list):
		print 'fail : values is not a list'
		return
	elif not isinstance(col,str):
		print 'fail : col is not a string'
		return

	nameCell = col + '1'
	startCell = col + '2'
	endCell = col + str(len(values)+1)

	#컬럼명
	worksheet.update_acell(nameCell,name)

	#데이터셀
	cell_list = worksheet.range(startCell+':'+endCell)

	for cell in cell_list:
		cell.value = values[cell.row-2]

	worksheet.update_cells(cell_list)
	print 'done: setColumn'

# 다음 인물 카테고리 페이지를 파싱한다.
def getUrls_Categories():
	url = 'http://100.daum.net/tag/1'
	soup = getSoup(url)
	urls = list()
	for a in soup.find('ul',attrs={'class':'list_type2'}).findAll('a'):
		urls.append('http://100.daum.net' + a['href'])
	return urls

# 다음 인물 리스트 페이지를 파싱한다.
def getUrls_People(url):
	soup = getSoup(url)
	urls = list()
	for a in soup.findAll('a',attrs = {'class':'link_register'}):
		urls.append('http://100.daum.net' + a['href'])
	return urls

# 인물 정보를 파싱한다.
def getInfos_Person(url):
	soup = getSoup(url)


