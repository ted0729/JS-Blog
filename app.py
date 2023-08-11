from flask import Flask, render_template, request, jsonify, session, redirect, url_for
app = Flask(__name__)

from bs4 import BeautifulSoup

from pymongo import MongoClient
import certifi

ca = certifi.where()

####### DB 경로 설정 필요 #######
client = MongoClient("mongodb+srv://sparta:test@cluster0.ewd45u6.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.dbsparta

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
SECRET_KEY = 'SPARTA'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib
from datetime import datetime, timedelta


#################################
##  HTML을 주는 부분             ##
#################################
@app.route('/')
def home():
    global nick
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        print(payload)
        user_info = db.members.find_one({"id": payload["id"]})
        print(user_info["name"])
        print("no except!! ")
        return render_template("index.html", nickname=user_info["name"])
    except Exception as ex: # 에러 종류
        print('에러가 발생 했습니다', ex) # ex는 발생한 에러의 이름을 받아오는 변수
        return render_template('index.html')

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

@app.route("/movie", methods=["GET"])
def movie_get():
    all_doc = list(db.doc.find({},{'_id':False}))
    return jsonify({'result':all_doc})


#################################
##  로그인을 위한 API            ##
#################################
# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    num_list = list(db.members.find({}, {'_id': False}))
    count = len(num_list) + 1

    db.members.insert_one({'id': id_receive, 'pwd': pw_hash, 'name': nickname_receive, 'mem_no' : count})

    return jsonify({'result': 'success'})

# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest() # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    result = db.members.find_one({'id': id_receive, 'pwd': pw_hash}) # id, 암호화된pw을 가지고 해당 유저를 찾습니다.

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24) # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# [유저 정보 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')

    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = db.members.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['name']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# 마이페이지 mypage POST --> 태현님 경로 확인 필요할 것 같습니다!
@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

@app.route("/mypage", methods=["POST"])
def mypage_post():
    nickname_receive = request.form['nickname_give']
    pwd_receive = request.form['pwd_give']

    doc = {
        'nickname': nickname_receive,
        'pwd': pwd_receive
    }
    
    db.mypage.insert_one(doc)
    return jsonify({'msg':'변경 완료!'})

@app.route("/mypage/delete", methods=["POST"])
def mypage_delete():
    return jsonify({'msg':'회원 탈퇴가 완료되었습니다.'})

# 마이페이지 mypage GET
@app.route("/mypage", methods=["GET"])
def mypage_get():
    all_mypage = list(db.fan.find({},{'_id':False}))
    return jsonify({'result':all_mypage})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)


