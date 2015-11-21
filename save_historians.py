# coding: utf-8
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

import urllib2
from BeautifulSoup import BeautifulSoup
import random
import string

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
	try:
		soup = getSoup(url)
		name = soup.find('h3',attrs={'class':'tit_desc'}).text
		desc = soup.find('strong',attrs={'class':'tit_other'})
		desc = desc.text if desc is not None else ''

		birth = 0
		death = 0
		nationality = ''

		for row in soup.find('table',attrs={'class':'list_summary'}).findAll('tr'):
			if row.span.text.encode('utf-8') == '출생' :
				if row.td.text.encode('utf-8').find('BC') >= 0:
					birth = row.td.text.encode('utf-8').replace('BC ',''),replace('.',' ').split(' ')[0]
				else:
					birth = row.td.text.encode('utf-8').replace('년',' ').split(' ')[0]
			elif row.span.text.encode('utf-8') == '사망' :
				if row.td.text.encode('utf-8').find('BC') >= 0:
					death = row.td.text.encode('utf-8').replace('BC ',''),replace('.',' ').split(' ')[0]
				else:
					death = row.td.text.encode('utf-8').replace('년',' ').split(' ')[0]
			elif row.span.text.encode('utf-8') == '국적' :
				nationality = row.td.text.encode('utf-8')

		values = [name,desc,str(birth),str(death),nationality]
	except:
		values = [name,'error',0,0,'error']
	return values

# 마지막페이지인지 구별한다.
def checkEndPage(url):
	try:
		soup = getSoup(url)
	except:
		return True
	if soup.find('span').text.encode('utf-8').find('없음') is None:
		return True
	else:
		return False

# 전체 인물 정보를 파싱한다.
def getAll():
	count = 0
	name = list()
	desc = list()
	birth = list()
	death = list()
	nationality = list()
	depth = list()

	#카테고리 파싱
	urls_categories = getUrls_Categories()
	for url_category in urls_categories:
		page = 0
		# 테스트용
		if count > 10:
			break
		#카테고리 내 페이지 파싱
		while True:
			# 테스트용
			if count > 10:
				break
			page += 1
			url_category = url_category+'?page='+str(page)
			if checkEndPage(url_category):
				break
			#인물 파싱
			urls_people = getUrls_People(url_category)
			for url_person in urls_people:
					values = getInfos_Person(url_person)
					name.append(values[0])
					desc.append(values[1])
					birth.append(values[2])
					death.append(values[3])
					nationality.append(values[4])
					depth.append(str(random.randrange(1,10)))
					count += 1
					if values[1] == 'error':
						print str(count) + '번째, 저장 실패: ' + url_person.encode('utf-8')
					else:
						print str(count)+' 개 저장 완료'
						print values

	# 스프레드시트 저장
	setColumn('A',name,'name')
	setColumn('B',birth,'birth')
	setColumn('C',death,'death')
	setColumn('D',nationality,'nationality')
	setColumn('E',depth,'depth')
	setColumn('F',desc,'desc')

	return 'Success: ' + str(count)



