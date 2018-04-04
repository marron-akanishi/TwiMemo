import time
from datetime import datetime
import json
import re
import tweepy as tp
import threading
import db_utils as db

# グローバル変数はスレッド動作時変更出来ないので注意
# パターンマッチ
status_url = re.compile(r"https://twitter.com/\w*/status/\d*")
message_url = re.compile(r"https://twitter.com/messages/media/\d*")
link_url = re.compile(r"https?://t.co/\S*")

def get_oauth(setting):
    """設定ファイルから各種キーを取得し、OAUTH認証を行う"""
    auth = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'])
    auth.set_access_token(setting['twitter_API']['Admin_Key'], setting['twitter_API']['Admin_Secret'])
    return auth

class StreamListener(tp.StreamListener):
    def __init__(self, api, setting):
        """コンストラクタ"""
        self.api = api
        self.me = self.api.me()
        self.hashtag = setting["HashTag"]
        self.base_url = setting['twitter_API']['Callback_URL'].replace("authed","detail/")

    def on_error(self, status_code):
        return True

    def on_timeout(self):
        return True
    
    def make_memo(self, status, isDM=False):
        memo = {}
        # 内容
        if isDM:
            memo["contents"] = status["text"]
        else:
            memo["contents"] = status.text.replace("#"+self.hashtag,"").strip()
        memo["contents"] = link_url.sub("", memo["contents"])
        # タイトル
        memo["title"] = memo["contents"]
        if len(memo["title"]) > 20:
            memo["title"] = memo["title"][:20]
        elif len(memo["title"]) == 0:
            memo["contents"] = "内容なし"
            memo["title"] = "タイトルなし"
        # 画像
        media_url = []
        if isDM:
            if "entities" in status and 'media' in status["entities"]:
                status_media = status["entities"]["media"]
                for image in status_media:
                    media_url.append(image['media_url'])
        else:
            if hasattr(status, "extended_entities"):
                if 'media' in status.extended_entities:
                    status_media = status.extended_entities
                    for image in status_media['media']:
                        media_url.append(image['media_url'])
        memo["media"] = ','.join(media_url)
        # URL
        urls = []
        if isDM:
            if "entities" in status and 'urls' in status["entities"]:
                status_urls = status["entities"]["urls"]
                for url in status_urls:
                    if not message_url.match(url['expanded_url']):
                        urls.append(url['expanded_url'])
        else:
            if hasattr(status, "entities"):
                if 'urls' in status.entities:
                    for url in status.entities["urls"]:
                        urls.append(url['expanded_url'])
        memo["url"] = '|'.join(urls)
        return memo

    def on_status(self, status):
        """UserStreamから飛んできたStatusを処理する"""
        if status.user.id == self.me.id:
            return
        get = False
        # ツイートにハッシュタグが入ってるか
        if hasattr(status, "entities") and "hashtags" in status.entities:
            for tag in status.entities['hashtags']:
                if tag['text'] == self.hashtag:
                    get = True
                    break
        if get:
            # DBのパスを生成
            dbpath = "DB/{}.db".format(status.user.id)
            # データ生成
            user = status.user.screen_name
            memo = {}
            memo["id"] = status.id
            memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # リプか？
            if hasattr(status, "in_reply_to_status_id") and status.in_reply_to_status_id is not None:
                status = self.api.get_status(status.in_reply_to_status_id)
            memo["source"] = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
            content = self.make_memo(status)
            memo.update(content)
            db.write_memo(dbpath, memo)
            # リプを送信
            self.api.update_status("@{} メモに登録しました[{}] {}".format(user, memo["time"], self.base_url+str(memo["id"])), memo["id"])

    def on_direct_message(self, status):
        """DMの処理"""
        status = status.direct_message
        if status["sender_id"] == self.me.id:
            return
        sender = status["sender_id"]
        # DBのパスを生成
        dbpath = "DB/{}.db".format(sender)
        # データ書き込み
        memo = {}
        memo["id"] = status["id"]
        memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 引用ツイートチェック
        try:
            url = status["entities"]["urls"][0]["expanded_url"]
            if status_url.match(url):
                memo["source"] = url
                status_id = url.split("/")[-1]
                status = self.api.get_status(status_id)
                content = self.make_memo(status)
                memo.update(content)
            else:
                raise ValueError
        except:
            memo["source"] = "DirectMessage"
            content = self.make_memo(status, True)
            memo.update(content)
        db.write_memo(dbpath, memo)
        # リプを送信
        self.api.send_direct_message(sender, text="メモに登録しました[{}] {}".format(memo["time"], self.base_url+str(memo["id"])))
    
    def on_event(self, event):
        """フォロバ"""
        if event.event == 'follow':
            if self.me.id != event.source["id"] and event.target["id"] == self.me.id:
                self.api.create_friendship(event.source["id"])

if __name__ == '__main__':
    setting = json.load(open("setting.json"))
    auth = get_oauth(setting)
    stream = tp.Stream(auth, StreamListener(tp.API(auth), setting), secure=True)
    print("start")
    stream.userstream()

class TLThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
 
    def run(self):
        setting = json.load(open("setting.json"))
        auth = get_oauth(setting)
        stream = tp.Stream(auth, StreamListener(tp.API(auth), setting), secure=True)
        if setting['Debug']:
            try:
                stream.userstream()
            except KeyboardInterrupt:
                exit()
        else:
            while True:
                try:
                    stream.userstream()
                except KeyboardInterrupt:
                    exit()
                except:
                    print('UserStream Error')
                    time.sleep(60)