#-*- coding: utf-8 -*-
from flask import Flask
from flask import render_template

import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import json

import urllib
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
	global sht
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
	return worksheet

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
def getAll(url=None,clean=False):
	count = 0
	name = list()
	desc = list()
	birth = list()
	death = list()
	nationality = list()
	depth = list()
	url_personal = list()

	#몽고디비 열기
	if clean:
		deleteMongo()
	openMongo()

	if url is None:
		#카테고리 파싱
		urls_categories = getUrls_Categories()
	else:
		#만약 url이 들어오면
		urls_categories = [url]

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
	#setWorkSheet()

	# 스프레드시트 저장
	#setColumn('A',name,'name')
	#setColumn('B',birth,'birth')
	#setColumn('C',death,'death')
	#setColumn('D',nationality,'nationality')
	#setColumn('E',depth,'depth')
	#setColumn('F',desc,'desc')
	#setColumn('G',url_personal,'url')
	copyMongoToSheet()

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

# 모든 사람의 위키 이름을 가져온다.
def getallwikiname():
	# 구글드라이브연결
	setWorkSheet()
	data = worksheet.get_all_values()
	wikinames = list()
	for row in data[1:]:
		name = row[0]
		wikiname = getinfoWiki(name)[0]
		print name.encode('utf-8') + ' -> ' + wikiname.encode('utf-8') + '\t|\t' + '진행중'
		wikinames.append(wikiname)
	setColumn('H',wikinames,'wikiname')
	return 'success'

# 문자열 찾기 함수
def findString(text,findstring,notlist = list()):
	result = False
	for string in findstring:
		if text.find(string) > -1:
			result = True
			break
	for string in notlist:
		if text.find(string) > -1:
			result = False
			break
	return result

# Bing의 인물검색 정보를 파싱한다.
# 참고: 파싱해서 가져올 때 텍스트는 유니코드로 가져온다.
def getinfoBing(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		url = u'http://www.bing.com/search?q='+schName
		url = urllib.quote(url.encode('utf8'), '/:')
		print url
		page = opener.open(url)
	       	soup = BeautifulSoup(page)
		name = soup.findAll('h2',attrs={'class':' b_entityTitle'})[0].text
		infobox = soup.find('ul',attrs={'class':'b_vList'}).findAll('li')

	       	birth_strs = ['출생:','Born:']
	       	death_strs = ['사망:','Died:']
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
       		if birth=='?' or death =='?':
       			raise Exception('년도 없음')
	       	value = [name,birth,death]
	except Exception, e:
		value = ['0','0',e.args[0]]
		print '인물 정보 파싱 실패: ' + e.args[0]
       	return value

def getinfoWiki(schName):
	try:
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		schName = schName.replace(' ','_').encode('utf-8')
		url = 'http://ko.wikipedia.org/wiki/'+schName
		page = opener.open(url)
	       	soup = BeautifulSoup(page)

	       	# 동음이의어 문서 파악
	       	isNavPage = findString(soup.findAll('div',attrs={'class':'mw-normal-catlinks'})[0].text.encode('utf-8'),['동음이의어','동명이인'])
	       	if isNavPage:
	       		maxcount = 3
	       		namelist = list()
	       		for a in soup.findAll('a'):
	       			if a.text.encode('utf-8').find(schName) > -1:
       					namelist.append(a.text)
	       				if len(namelist) == maxcount:
	       					break
	       		value = ['1',namelist,'0','0',url]
	       		return value

	       	# 위키 이름
	       	name = soup.find('h1',attrs={'id':'firstHeading'}).text

	       	# 기본 분석
	       	birth = False
		death = False
		nationality = False
		for p in soup.findAll('p'):
			if p.b is not None and p.text.find('~') > -1:
				# 국가 찾기
				for a in p.findAll('a'):
					a = a.text.encode('utf-8')
					if nationality == False:
						temp = getNationality(a)
						if temp:
							nationality = tranNationality(temp)
							break

				# 생년 찾기
				p = str(p).split('. ')[0]
				start = p.find('(')
				end = start + 1500
				r = p[start:end]
				# 출생년도 찾기
				r_birth = str(r).split('~')[0]
				for a in BeautifulSoup(r_birth).findAll('a'):
					a = a.text.encode('utf-8')
					if findString(a,['년']):
						birth = int(a.split('년')[0])
						break
				# 사망년도 찾기
				r_death = str(r).split('~')[1]
				for a in BeautifulSoup(r_death).findAll('a'):
					a = a.text.encode('utf-8')
					if findString(a,['년']):
						death = int(a.split('년')[0])
						break
				break

		# 생존하고 있는 사람
		if birth and not death:
			death = 2099
		elif not birth and not death:
			raise Exception

		# 국가 디폴트 설정
		if not nationality:
			nationality = '기타'
		nationality = nationality.decode('utf-8')

	       	value = [name,birth,death,nationality,url]
	except Exception, e:
		schName = schName.replace(' ','_')
		url = 'http://ko.wikipedia.org/wiki/'+schName
		value = ['0','0','0','0',url]
		print '인물 정보 파싱 실패'
       	return value

# 예전 국가를 검색한다.
def tranNationality(nation):
	if findString(nation,['조선','고려','고구려','신라','백제','대한']):
		nation = '한국'
	elif findString(nation,['로마']):
		nation = '이탈리아'
	elif findString(nation,['중화인민공화국']):
		nation = '중국'
	return nation


# 국가를 찾는다.
def getNationality(nation):
	nationalities = ['가나','가봉','가이아나','감비아','과테말라','그레나다','그리스','기니','기니비사우','나미비아','나이지리아','남수단','남아프리카공화국','네덜란드','네팔','노르웨이','뉴질랜드','니제르','니카라과','덴마크','도미니카 공화국','도미니카 연방','독일','동티모르','라오스','라이베리아','라트비아','러시아','레바논','레소토','루마니아','룩셈부르크','르완다','리비아','리투아니아','마다가스카르','마셜 제도','마케도니아','말라위','말레이시아','말리','멕시코','모로코','모리셔스','모리타니','모잠비크','몬테네그로','몰도바','몰디브','몰타','몽골','미국','미얀마','바누아투','바레인','바베이도스','바하마','방글라데시','베냉','베네수엘라','베트남','벨기에','벨라루스','벨리즈','보스니아 헤르체고비나','보츠와나','볼리비아','부룬디','부르키나파소','부탄','불가리아','브라질','브루나이','사모아','사우디아라비아','산마리노','상투메프린시페','세네갈','세르비아','세이셸','세인트 루시아','세인트 키츠 네비스','솔로몬 제도','수단','수리남','스리랑카','스와질란드','스웨덴','스위스','스페인','슬로바키아','슬로베니아','시리아','시에라리온','싱가포르','아랍에미리트','아르메니아','아르헨티나','아이슬란드','아이티','아일랜드 공화국','아제르바이잔','아프가니스탄','알바니아','알제리','앙골라','앤티가 바부다','에리트레아','에스토니아','에콰도르','에티오피아','엘살바도르','영국','예멘','오만','오스트리아','온두라스','요르단','우간다','우루과이','우즈베키스탄','우크라이나','이라크','이란','이스라엘','이집트','이탈리아','인도','인도네시아','일본','자메이카','잠비아','적도 기니','조지아','중국','중앙아프리카 공화국','지부티','짐바브웨','차드','체코','칠레','카메룬','카보베르데','카자흐스탄','카타르','캄보디아','캐나다','케냐','코모로','코소보','코스타리카','코트디부아르','콜롬비아','콩고 공화국','콩고 민주 공화국','쿠웨이트','크로아티아','키르기스스탄','키리바시','키프로스','타지키스탄','탄자니아','태국','터키','토고','통가','투르크메니스탄','투발루','튀니지','트리니다드 토바고','파나마','파라과이','파키스탄','파푸아뉴기니','팔라우','페루','포르투갈','폴란드','프랑스','피지','핀란드','필리핀','한국','헝가리','호주','홍콩']
	nationalities += ['조선','고려','고구려','신라','백제','대한']
	nationalities += ['로마']
	nationalities += ['중화인민공화국']
	for n in nationalities:
		if nation.find(n) > -1:
			return n
	return False

# 인물을 기록한다.
def addHistory(name):
	# 인물 검사
	setWorkSheet()
	value = getinfoWiki(name)
	wikiname = value[0]
	url = value[4]
	result = dict()
	if wikiname == '0':
		result['resultCode'] = '4' # 파싱 실패
		result['resultMsg'] = '위키에서 올바른 데이터를 찾을 수 없습니다. <br/> 여기를 눌러 페이지를 확인하세요 <br/>( 참고: 기원전은 지원 안한다는 사실 )' # 파싱 실패
		result['url'] = url # 파싱 실패
	elif wikiname =='1':
		result['resultCode'] = '3'
		result['resultMsg'] = '올바른 데이터가 없나요? <br/> 여기를 눌러 페이지를 확인하세요' # 파싱 실패
		result['namelist'] = value[1]
		result['url'] = url # 파싱 실패
	else:
		birth = int(value[1])
		death = int(value[2])
		nationality = value[3]
		if hasDuplication(wikiname):
			result['resultCode'] = '2' # 중복
			result['resultMsg'] = str(birth)+'~'+ ( str(death) if death < 2016 else '현재' )
			result['wikiname'] = wikiname
			result['nationality'] = nationality
		else:
			url = 'http://ko.wikipedia.org/wiki/'+wikiname
			depth = getDepth(nationality,birth,death)
			addOne(wikiname,birth,death,nationality,depth,'',url)
			result['resultCode'] = '1' # 성공
			result['wikiname'] = wikiname
			result['nationality'] = nationality
			result['resultMsg'] = str(birth)+'~'+ ( str(death) if death < 2016 else '현재' )
			result['url'] = url # 파싱 실패
	return result

# 인물 한 명을 더한다.
def addOne(name,birth,death,nationality,depth,desc,url):
	data = worksheet.get_all_values()
	addrow = len(data) + 1
	worksheet.update_cell(addrow, 1, name)
	worksheet.update_cell(addrow, 2, birth)
	worksheet.update_cell(addrow, 3, death)
	worksheet.update_cell(addrow, 4, nationality)
	worksheet.update_cell(addrow, 5, depth)
	worksheet.update_cell(addrow, 6, desc)
	worksheet.update_cell(addrow, 7, url)

# 겹치는 인물이 있는지 확인한다.
def hasDuplication(wikiname):
	try:
		worksheet.find(wikiname)
		return True
	except:
		return False

# 문의하기를 기록한다.
def saveClaim(claimtype,msg):
	result = dict()
	try:
		setWorkSheet()
		worksheet_claim = sht.worksheet("msg")
		data = worksheet_claim.get_all_values()
		addrow = len(data) + 1
		worksheet_claim.update_cell(addrow, 1, claimtype)
		worksheet_claim.update_cell(addrow, 2, msg)
		result['resultCode'] = '1'
		result['resultMsg'] = '남겨두었습니다'
	except:
		result['resultCode'] = '0'
		result['resultMsg'] = '서버 통신에 실패했습니다'
	return result

# 한 명의 Depth를 구한다.
def getDepth(nationality,birth,death):
	setWorkSheet()
	data = worksheet.get_all_values()
	# 일단 전체 데이터 중 해당 국가의 데이터를 담는다.
	data_nation = list()
	depth_max = 0
	depth_set = 0
	for row in data[1:]:
		if row[3] == nationality:
			data_nation.append(row)
			row_depth = int(row[4])
			if depth_max < row_depth:
				depth_max = row_depth

	if depth_max > 0:
		for i in range(1,depth_max):
			depth_random = random.randint(1, depth_max)
			stop = True
			for row in data_nation:
				row_depth = int(row[4])
				row_birth = int(row[1])
				row_death = int(row[2])
				# 겹치는 애들이 있으면
				if row_depth == depth_random and not ((row_death+100) < birth or row_birth > (death+100)):
					stop = False
					break
			if stop:
				depth_set = depth_random
				break
		if depth_set == 0:
			depth_set = depth_max + 1
	else:
		depth_set = 1

	return depth_set

# 전체의 Depth를 구해서 다시 입력한다.
def setDepthAgain():
	setWorkSheet()
	worksheet_backup = sht.worksheet("back_up")
	data = worksheet_backup.get_all_values()
	for row in data:
		name = row[0]
		nationality =  row[3]
		addHistory(name,nationality)
		print name + ' / ' + nationality

#setDepthAgain()




###### [ 시작 ] #####
#url = 'http://100.daum.net/book/187/list' ## 세계사 100인
#url = 'http://100.daum.net/book/130/list' ## 한국사
#getAll(url)
#getallwikiname()
