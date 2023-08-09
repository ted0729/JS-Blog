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

if __name__ == '__main__':
	app.run('0.0.0.0', port=5001, debug=True)