import os
import json
import DBreader as db
import tweepy as tp
import flask
from functools import wraps
from datetime import datetime
import streaming

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 自身の名称を app という名前でインスタンス化する
app = flask.Flask(__name__)
setting = json.load(open("setting.json"))
app.secret_key = setting['SecretKey']
app.debug = setting['Debug'] # デバッグモード

# 回収
if(setting['Debug'] == False):
    t1 = streaming.TLThread()
    t1.setDaemon(True)
    t1.start()

# 認証後に使用可能
def tp_api():
    auth = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'], setting['twitter_API']['Callback_URL'])
    auth.set_access_token(flask.session['key'],flask.session['secret'])
    return tp.API(auth)

def login_check(func):
    @wraps(func)
    def checker(*args, **kwargs):
        # きちんと認証していればセッション情報がある
        try:
            if flask.session['userID'] is None:
                return flask.redirect(flask.url_for('index'))
        except:
            return flask.redirect(flask.url_for('index'))
        return func(*args, **kwargs)
    return checker

# ここからウェブアプリケーション用のルーティングを記述
# トップページ
@app.route('/')
def index():
    key = flask.request.cookies.get('key')
    secret = flask.request.cookies.get('secret')
    if key is None or secret is None:
        return flask.render_template('index.html', top=True)
    else:
        flask.session['key'] = key
        flask.session['secret'] = secret
        return flask.redirect(flask.url_for('twitter_authed', cookie=True))

# このページについて
@app.route('/about')
def about():
    return flask.render_template('about.html', top=True)

# エラー
@app.route('/error')
def error():
    return flask.render_template('error.html')

# twitter認証
@app.route('/twitter_auth', methods=['GET'])
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
        return flask.redirect(redirect_url)
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
    response = flask.make_response(flask.redirect(flask.url_for('user_page')))
    response.set_cookie('key', flask.session['key'])
    response.set_cookie('secret', flask.session['secret'])
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
@app.route('/list')
@login_check
def user_page():
    dbname = flask.session['userID']
    try:
        memolist = db.get_list("DB/" + dbname + ".db")
    except:
        memolist = None
    return flask.render_template('list.html',list=memolist)

# メモ詳細
@app.route('/detail/<id>')
@login_check
def memo_detail(id):
    dbname = flask.session['userID']
    try:
        detail = db.get_detail(int(id), "DB/"+dbname+".db")
    except:
        return flask.redirect("/error")
    return flask.render_template('detail.html', memo=detail)

# メモ編集
@app.route('/edit/<id>')
@login_check
def memo_editscreen(id):
    dbname = flask.session['userID']
    try:
        detail = db.get_detail(int(id), "DB/"+dbname+".db")
    except:
        return flask.redirect("/error")
    return flask.render_template('edit.html', memo=detail)

@app.route('/edited/<id>', methods=['POST'])
@login_check
def memo_edit(id):
    memo = {}
    dbname = flask.session['userID']
    memo["id"] = int(id)
    memo["contents"] = flask.request.form["contents"]
    memo["media"] = flask.request.form["media"]
    if not memo["media"].startswith("http"):
        memo["media"] = "null"
    memo["url"] = flask.request.form["url"]
    memo["source"] = "編集済み"
    memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        db.update_memo("DB/"+dbname+".db", int(id), memo)
        detail = db.get_detail(int(id), "DB/"+dbname+".db")
    except:
        return flask.redirect("/error")
    return flask.redirect("/detail/"+id)

# メモ削除
@app.route('/delete/<id>', methods=['DELETE'])
@login_check
def memo_delete(id):
    dbname = flask.session['userID']
    db.del_memo("DB/"+dbname+".db", int(id))
    return "OK"

if __name__ == '__main__':
    # debug server
    app.run(host='0.0.0.0') # どこからでもアクセス可能に
