import os
import json
import db_utils as db
import tweepy as tp
import flask
import uuid
import html
import urllib
from functools import wraps
from datetime import datetime
import streaming

os.chdir(os.path.dirname(os.path.abspath(__file__)))

ErrorMessage = {
    "-1": "不明なエラーが発生しました。",
    "101": "メモの詳細取得に失敗しました。",
    "102": "データベースの更新に失敗しました。",
    "103": "データベース名が不正です。ログインし直してください。",
    "201": "Twitter認証に失敗しました。ログインし直してください。"
}

sql_escape = str.maketrans({
    '%': '$%',
    '_': '$_',
    '$': '$$',
})

# 自身の名称を app という名前でインスタンス化する
app = flask.Flask(__name__)
setting = json.load(open("setting.json"))
app.secret_key = setting['SecretKey']
app.debug = setting['Debug'] # デバッグモード

# TL監視
if setting['Debug'] == False:
    t1 = streaming.TLThread()
    t1.setDaemon(True)
    t1.start()

# Twitter認証
def tp_api():
    auth = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
    if flask.session.get('key') is None or flask.session.get('secret') is None:
        return flask.redirect(flask.url_for("error", code="201"))
    auth.set_access_token(flask.session.get('key'),flask.session.get('secret'))
    return tp.API(auth)

# ログインチェック
def login_check(func):
    @wraps(func)
    def checker(*args, **kwargs):
        # きちんと認証していればセッション情報がある
        if flask.session.get('userID') is None:
            if "id" in kwargs:
                flask.session['memo_id'] = kwargs['id']
            return flask.redirect(flask.url_for('twitter_oauth'))
        return func(*args, **kwargs)
    return checker

# ここからルーティングを記述
# トップページ
@app.route('/')
def index():
    key = flask.request.cookies.get('key')
    secret = flask.request.cookies.get('secret')
    if key is None or secret is None:
        return flask.render_template('index.html')
    else:
        flask.session['key'] = key
        flask.session['secret'] = secret
        return flask.redirect(flask.url_for('twitter_authed', cookie=True))

# このページについて
@app.route('/help')
def help():
    return flask.render_template('help.html')

# エラー
@app.errorhandler(404)
@app.route('/error', methods=['GET'])
def error(code = "-1"):
    code = flask.request.args.get('code')
    if not code:
        code = "-1"
    return flask.render_template('error.html', message=ErrorMessage[code])

# twitter認証
@app.route('/twitter_auth')
def twitter_oauth():
    # cookieチェック
    key = flask.request.cookies.get('key')
    secret = flask.request.cookies.get('secret')
    if key is None or secret is None:
        # tweepy でアプリのOAuth認証を行う
        auth_temp = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
        # 連携アプリ認証用の URL を取得
        redirect_url = auth_temp.get_authorization_url()
        # 認証後に必要な request_token を session に保存
        flask.session['request_token'] = auth_temp.request_token
        # リダイレクト
        return flask.redirect(redirect_url.replace("authorize","authenticate"))
    else:
        flask.session['key'] = key
        flask.session['secret'] = secret
        return flask.redirect(flask.url_for('twitter_authed', cookie=True))

# twitter認証完了
@app.route('/authed', methods=['GET'])
def twitter_authed():
    # 認証情報取得
    if flask.request.args.get('cookie') != "True":
        auth_temp = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
        auth_temp.request_token = flask.session['request_token']
        auth_temp.get_access_token(flask.request.args.get('oauth_verifier'))
        flask.session['key'] = auth_temp.access_token
        flask.session['secret'] = auth_temp.access_token_secret
        flask.session['request_token'] = None
    # 認証ユーザー取得
    flask.session['name'] = tp_api().me().screen_name
    flask.session['userID'] = tp_api().me().id_str
    flask.session['version'] = setting['Version']
    if flask.session.get('memo_id') is not None:
        response = flask.make_response(flask.redirect(flask.url_for('memo_detail', id=int(flask.session.get('memo_id')))))
        flask.session['memo_id'] = None
    else:
        response = flask.make_response(flask.redirect(flask.url_for('memo_list')))
    response.set_cookie('key', flask.session.get('key'))
    response.set_cookie('secret', flask.session.get('secret'))
    return response

# ログアウトボタン
@app.route('/logout')
def logout():
    response = flask.make_response(flask.redirect(flask.url_for('index')))
    response.set_cookie('key', '', expires=0)
    response.set_cookie('secret', '', expires=0)
    flask.session.clear()
    return response

# こっから下は認証が必要
# リスト
@app.route('/list', methods=['GET'])
@login_check
def memo_list():
    dbname = flask.session.get('userID')
    search = flask.request.args.get('search','')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    try:
        if search:
            search = urllib.parse.unquote(search).translate(sql_escape)
            memolist = db.search_list("DB/" + dbname + ".db", search)
        else:
            memolist = db.get_list("DB/" + dbname + ".db")
    except:
        memolist = []
    return flask.render_template('list.html',list=memolist)

# メモ詳細
@app.route('/detail/<id>')
@login_check
def memo_detail(id):
    dbname = flask.session.get('userID')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    try:
        detail = db.get_detail("DB/"+dbname+".db", int(id))
    except:
        return flask.redirect(flask.url_for("error", code="101"))
    detail["contents"] = html.escape(detail["contents"]).replace("\n","<br>")
    return flask.render_template('detail.html', memo=detail)

# メモ編集
@app.route('/edit/<id>')
@login_check
def memo_edit(id):
    dbname = flask.session.get('userID')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    try:
        detail = db.get_detail("DB/"+dbname+".db", int(id))
    except:
        return flask.redirect(flask.url_for("error", code="101"))
    detail["contents"] = detail["contents"].replace("\n","\r\n")
    return flask.render_template('edit.html', memo=detail)

# 編集登録
@app.route('/edited/<id>', methods=['POST'])
@login_check
def memo_update(id):
    memo = {}
    dbname = flask.session.get('userID')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    memo["id"] = int(id)
    memo["contents"] = flask.request.form["contents"].replace("\r\n","\n")
    if flask.request.form["title"] != "":
        memo["title"] = flask.request.form["title"]
    elif len(memo["contents"]) > 20:
        memo["title"] = memo["contents"][:20]
    else:
        memo["title"] = memo["contents"]
    memo["media"] = flask.request.form["media"]
    memo["url"] = flask.request.form["url"]
    memo["source"] = "edited"
    memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        db.update_memo("DB/"+dbname+".db", int(id), memo)
        detail = db.get_detail("DB/"+dbname+".db", int(id))
    except:
        return flask.redirect(flask.url_for("error", code="102"))
    return flask.redirect("/detail/"+id)

# メモ追加
@app.route('/new')
@login_check
def memo_new():
    memo = {}
    memo["id"] = int(datetime.now().timestamp())
    return flask.render_template('new.html', memo=memo)

# 画像アップロード
def upload_file(file):
    url = ""
    if file.filename.split('.')[-1] in ['png', 'jpg']:
        filename = str(uuid.uuid4()) + "." + file.filename.split('.')[-1]
        file.save(setting['UploadDir'] + "/" + filename)
        url = setting['UploadServer'] + filename
    return url

# 新規登録
@app.route('/make/<id>', methods=['POST'])
@login_check
def memo_add(id):
    memo = {}
    dbname = flask.session.get('userID')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    memo["id"] = int(id)
    memo["contents"] = flask.request.form["contents"].replace("\r\n","\n")
    if flask.request.form["title"] != "":
        memo["title"] = flask.request.form["title"]
    elif len(memo["contents"]) > 20:
        memo["title"] = memo["contents"][:20]
    else:
        memo["title"] = memo["contents"]
    memo["media"] = []
    count = int(flask.request.form["count"])
    for i in range(count):
        try:
            memo["media"].append(upload_file(flask.request.files["media_"+str(i)]))
        except:
            continue
    memo["media"] = ",".join(memo["media"])
    memo["url"] = flask.request.form["url"]
    memo["source"] = "web"
    memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        db.write_memo("DB/"+dbname+".db", memo)
    except:
        return flask.redirect(flask.url_for("error", code="102"))
    return flask.redirect("/list")

# メモ削除
@app.route('/delete/<id>', methods=['DELETE'])
@login_check
def memo_delete(id):
    dbname = flask.session.get('userID')
    if dbname is None:
        return flask.redirect(flask.url_for("error", code="103"))
    db.del_memo("DB/"+dbname+".db", int(id))
    return "OK"

# 画像サーバー
@app.route('/uploads/<filename>')
@login_check
def uploaded_file(filename):
    return flask.send_from_directory(setting['UploadDir'], filename)

# デバッグ用
if __name__ == '__main__':
    app.run(host='0.0.0.0')
