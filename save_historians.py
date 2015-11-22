#-*- coding: utf-8 -*-
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

import urllib2
from BeautifulSoup import BeautifulSoup
import random
import string
import sys

from pymongo import MongoClient

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
	print 'start: setColumn: ' + col
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

	#테스트용
	print values

	for cell in cell_list:
		print 'cell row: ' + str(cell.row) + ' / ' + values[cell.row-2]
		cell.value = values[cell.row-2]

	worksheet.update_cells(cell_list)
	print 'done: setColumn: ' + col

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
	name = soup.find('h3',attrs={'class':'tit_desc'}).text
	try:
		desc = soup.find('strong',attrs={'class':'tit_other'})
		desc = desc.text.encode('utf-8').replace('\t','').replace('  ','').decode('utf-8') if desc is not None else ''

		birth = 0
		death = 0
		nationality = ''

		for row in soup.find('table',attrs={'class':'list_summary'}).findAll('tr'):
			if row.span.text.encode('utf-8') == '출생' :
				birth = getYear(row.td.text.encode('utf-8'),'birth')
			elif row.span.text.encode('utf-8') == '사망' :
				death = getYear(row.td.text.encode('utf-8'),'death')
			elif row.span.text.encode('utf-8') == '국적' :
				nationality = row.td.text.encode('utf-8').replace(',','').replace('(','').split(' ')[0].decode('utf-8')

		values = [name,desc,str(birth),str(death),nationality]
	#요약 박스가 없을 때
	except:
		values = [name,'error','0','0','error']
	return values

# 출생, 사망 연도를 파싱한다.
def getYear(text,bdtype):
	if text.find('BC') >=0:
		year = text.replace('BC ','').replace('(',' ').replace(',',' ').replace('.',' ').replace('/',' ').split(' ')[0]
		year = '-1'+year
	else:
		year = text.replace('년',' ').replace('(',' ').replace(',',' ').replace('.',' ').replace('/',' ').split(' ')[0]
	if bdtype == 'death' and str(year) == '현재':
		year = '2015'
	try:
		year = int(year)
		return year
	except:
		print '연도 파싱 불가:' + text
		raise Exception

# 마지막페이지인지 구별한다.
def checkEndPage(url):
	try:
		soup = getSoup(url)
	except:
		# URL이 없을 때
		return True
	if not soup.find('strong',attrs={'class':'tit_nosubject'}) is None:
		# 페이지가 없음
		return True
	else:
		return False

# 몽고디비 열기
def openMongo():
	global db
	global collection

	client = MongoClient()
	client = MongoClient('localhost', 27017)

	db = client.historyofgreats
	collection = db.info

# 몽고디비 저장
def saveMongo(count,name,birth,death,nationality,depth,desc,url,parent_url):
	data = {"count":count,"name":name,"birth":birth,"death":death,"nationality":nationality,"depth":depth,"desc":desc,"url":url,"parent_url":parent_url}
	collection.insert(data)

# 몽고디비 데이터 확인
def printMongo():
	openMongo()
	for doc in collection.find():
        		print doc

# 몽고디비 데이터 삭제
def deleteMongo():
	openMongo()
	db.info.remove({})

# 전체 인물 정보를 파싱한다.
def getAll():
	count = 0
	name = list()
	desc = list()
	birth = list()
	death = list()
	nationality = list()
	depth = list()
	url_personal = list()

	#몽고디비 열기
	deleteMongo()
	openMongo()

	#카테고리 파싱
	urls_categories = getUrls_Categories()
	for url_category_base in urls_categories:
		print '카테고리 페이지 시작:' + url_category_base.encode('utf-8')
		page = 0
		while True:
			page += 1
			url_category = url_category_base+'?page='+str(page)
			#마지막페이지 일 경우 브레이크
			if checkEndPage(url_category):
				print '컨텐츠 페이지 없음:' + url_category.encode('utf-8')
				break
			else:
				print '컨텐츠 페이지 시작:' + url_category.encode('utf-8')
			#인물 파싱
			urls_people = getUrls_People(url_category)
			for url_person in urls_people:
					count += 1
					values = getInfos_Person(url_person)
					if values[1] == 'error':
						print str(count) + '번째, 저장 실패: ' + url_person.encode('utf-8')
					else:
						name.append(values[0])
						desc.append(values[1])
						birth.append(values[2])
						death.append(values[3])
						nationality.append(values[4])
						depth.append(str(random.randrange(1,10)))
						url_personal.append(url_person)
						saveMongo(count,values[0],values[2],values[3],values[4],'',values[1],url_person,url_category)
						print str(count)+' 개 저장 완료' + json.dumps(values)
		break
	# 스프레드시트 부르기
	setWorkSheet()

	# 스프레드시트 저장
	setColumn('A',name,'name')
	setColumn('B',birth,'birth')
	setColumn('C',death,'death')
	setColumn('D',nationality,'nationality')
	setColumn('E',depth,'depth')
	setColumn('F',desc,'desc')
	setColumn('G',url_personal,'url')

	return 'Success: ' + str(count)

# 몽고디비에 있는 데이터를 저장한다.
def copyMongoToSheet():
	#몽고디비 부르기
	openMongo()

	count = list()
	name = list()
	desc = list()
	birth = list()
	death = list()
	nationality = list()
	depth = list()
	url_personal = list()

	for doc in collection.find():
		count.append(doc['count'])
		name.append(doc['name'])
		desc.append(doc['desc'])
		birth.append(doc['birth'])
		death.append(doc['death'])
		nationality.append(doc['nationality'])
		depth.append(str(random.randrange(1,10)))
		url_personal.append(doc['url'])

	# 스프레드시트 부르기
	setWorkSheet()
	setColumn('A',name,'name')
	setColumn('B',birth,'birth')
	setColumn('C',death,'death')
	setColumn('D',nationality,'nationality')
	setColumn('E',depth,'depth')
	setColumn('F',desc,'desc')
	setColumn('G',url_personal,'url')


