# coding: utf-8
from flask import Flask
from flask import render_template
from flask import request

from bson.json_util import dumps

import datetime
import pymongo

app = Flask(__name__)

@app.route("/")
def hello():
    	return "apache is running"

# 사진을 띄워준다
@app.route("/main")
def main():
 	return render_template('main.html')

# 사진을 띄워준다
@app.route("/img")
def img():
 	return render_template('show.html',url='../static/1.jpg')

#데이터 입력
@app.route("/<page>/insert", methods=["POST","GET"])
def insert(page):
	name 	= request.args.get('name')
	start   	= request.args.get('start')	#20000101
	end  	= request.args.get('end')	#20100902
	category  = request.args.get('category')

	#set today
	today 		= datetime.date.today()
	today		= today.year + today.month + today.day

	#parameter check
	name   	= (name,'')[name==None]
	start   		= (start,'')[start==None]
	end   		= (end,today)[end==None]
	category   	= (category,'')[category==None]

	#db connection
	connection = pymongo.MongoClient("mongodb://localhost")
	db = connection.history
	collection = db.data
	doc = {'page':page,'name':name,'start':start,'end':end,'category':category}
    	collection.insert(doc)

     	return "1"

#데이터 삭제
@app.route("/delete/<page>/<name>")
def delete(page,name):
	#db connection
	connection = pymongo.MongoClient("mongodb://localhost")
	db = connection.history
	collection = db.data
	collection.remove({'name':name,'page':page})
	return "1"

#데이터 조회
@app.route("/show/<page>")
def show(page):
	#db connection
	connection = pymongo.MongoClient("mongodb://localhost")
	db = connection.history
	collection = db.data
	cursor = collection.find({'page':page},{'start':1,'end':1,'name':1,'category':1,'_id':0}).sort("start", pymongo.ASCENDING)
	return dumps(cursor)


if __name__ == "__main__":
    app.run(debug = True)
