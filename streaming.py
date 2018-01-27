import os
import time
from datetime import datetime
import json
import re
import tweepy as tp
import threading
import db_utils as db

# スタート文字列
hashtag = "memo"
# パターン
status_url = re.compile(r"https://twitter.com/\w*/status/\d*")
message_url = re.compile(r"https://twitter.com/messages/media/\d*")

def get_oauth(setting):
    """設定ファイルから各種キーを取得し、OAUTH認証を行う"""
    auth = tp.OAuthHandler(setting['twitter_API']['CK'], setting['twitter_API']['CS'])
    auth.set_access_token(setting['twitter_API']['Admin_Key'], setting['twitter_API']['Admin_Secret'])
    return auth

class StreamListener(tp.StreamListener):
    def __init__(self, api):
        """コンストラクタ"""
        self.api = api
        self.me = self.api.me()
    
    def make_memo(self, status):
        memo = {}
        memo["contents"] = status.text.replace("#"+hashtag,"").strip()
        memo["title"] = memo["contents"]
        if len(memo["title"]) > 20:
            memo["title"] = memo["title"][:17] + "..."
        media_url = []
        if hasattr(status, "extended_entities"):
            if 'media' in status.extended_entities:
                status_media = status.extended_entities
                for image in status_media['media']:
                    media_url.append(image['media_url'])
        memo["media"] = ','.join(media_url)
        urls = []
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
                if tag['text'] == hashtag:
                    get = True
                    break
        if get:
            # DBのパスを生成
            dbpath = "DB/{}.db".format(status.user.id)
            # データ生成
            user = status.user.screen_name
            memo = {}
            memo["id"] = status.id
            memo["source"] = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
            memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # リプか？
            if hasattr(status, "in_reply_to_status_id") and status.in_reply_to_status_id is not None:
                status = self.api.get_status(status.in_reply_to_status_id)
            content = self.make_memo(status)
            memo.update(content)
            db.write_memo(dbpath, memo)
            # リプを送信
            self.api.update_status("@{} メモに登録しました[{}]".format(status.user.screen_name,memo["time"]), memo["id"])

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
        # 引用ツイートチェック
        try:
            url = status["entities"]["urls"][0]["expanded_url"]
            if status_url.match(url):
                status_id = url.split("/")[-1]
                status = self.api.get_status(status_id)
                content = self.make_memo(status)
                memo.update(content)
                memo["source"] = url
            else:
                raise ValueError
        except:
            memo["contents"] = status["text"]
            memo["title"] = memo["contents"]
            if len(memo["title"]) > 20:
                memo["title"] = memo["title"][:17] + "..."
            media_url = []
            if "entities" in status and 'media' in status["entities"]:
                status_media = status["entities"]["media"]
                for image in status_media:
                    media_url.append(image['media_url'])
            memo["media"] = ",".join(media_url)
            urls = []
            if "entities" in status and 'urls' in status["entities"]:
                status_urls = status["entities"]["urls"]
                for url in status_urls:
                    if not message_url_url.match(url):
                        urls.append(url['expanded_url'])
            memo["url"] = "|".join(urls)
            memo["source"] = "DirectMessage"
        memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.write_memo(dbpath, memo)
        # リプを送信
        self.api.send_direct_message(sender, text="メモに登録しました[{}]".format(memo["time"]))
    
    def on_event(self, event):
        """フォロバ"""
        if event.event == 'follow':
            if self.me.id != event.source["id"] and event.target["id"] == self.me.id:
                self.api.create_friendship(event.source["id"])

if __name__ == '__main__':
    setting = json.load(open("setting.json"))
    hashtag = setting["HashTag"]
    auth = get_oauth(setting)
    stream = tp.Stream(auth, StreamListener(tp.API(auth)), secure=True)
    print("start")
    stream.userstream()

class TLThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
 
    def run(self):
        setting = json.load(open("setting.json"))
        hashtag = setting["HashTag"]
        auth = get_oauth(setting)
        stream = tp.Stream(auth, StreamListener(tp.API(auth)), secure=True)
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