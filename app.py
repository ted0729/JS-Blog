from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

@app.route('/')
def home():
	return render_template('index.html')

@app.route("/movie", methods=["POST"])
def movie_post():
	sample_receive = request.form['sample_give']
	print(sample_receive)
	return jsonify({'msg':'POST 연결 완료!'})

@app.route("/movie", methods=["GET"])
def movie_get():
	return jsonify({'msg':'어서와요 알찬 하루!'})

@app.route("/board")
def board():
    return render_template('board_insert.html')

@app.route("/board/save", methods=["GET"])
def save_get():
	return jsonify({'msg':'연결완료!'})

@app.route("/board/save", methods=["POST"])
def save_post():
	title_receive = request.form['title_give']
	imgurl_receive = request.form['imgurl_give']
	detail_receive = request.form['detail_give']

	doc_list = list(db.doc.find({}, {'_id': False}))
	count = len(doc_list) + 1

	doc = {
		'no':count,
        'title':title_receive,
        'imgurl' : imgurl_receive,
		'detail' : detail_receive
    }
	db.doc.insert_one(doc)
	
	return jsonify({'msg': '저장완료!'})

@app.route("/list_detail/<temp>")
def detail_get(temp):
	detailDoc = db.doc.find_one({'no':int(temp)},{'_id': False})
	return render_template('board_detail.html',result = detailDoc,
												title = detailDoc['title'],
												no = detailDoc['no'],
												imgurl = detailDoc['imgurl'],
												detail = detailDoc['detail'])
								
@app.route("/board/update/<temp>")
def update_get(temp):
	detailDoc = db.doc.find_one({'no':int(temp)},{'_id': False})
	return render_template('board_update.html',result = detailDoc,
												title = detailDoc['title'],
												no = detailDoc['no'],
												imgurl = detailDoc['imgurl'],
												detail = detailDoc['detail'])

@app.route("/board/update", methods=["POST"])
def update_post():
	no_receive = request.form['no_give']
	title_receive = request.form['title_give']
	imgurl_receive = request.form['imgurl_give']
	detail_receive = request.form['detail_give']

	db.doc.update_one({'no':int(no_receive)},{'$set':{'title':title_receive, 'imgurl':imgurl_receive, 'detail':detail_receive}})
	
	return jsonify({'msg': '업데이트완료!'})

@app.route("/board/del", methods=["POST"])
def del_post():
	no_receive = request.form['no_give']

	db.doc.delete_one({'no':int(no_receive)})
	print(no_receive)
	return jsonify({'msg': '삭제완료!'})

if __name__ == '__main__':
	app.run('0.0.0.0', port=5001, debug=True)