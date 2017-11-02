import os
import time
from datetime import datetime
import hashlib
import urllib
import json
import tweepy as tp
import threading
import DBreader as db

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

    def on_status(self, status):
        """UserStreamから飛んできたStatusを処理する"""
        # ツイートに#memoから始まってるかどうか
        if(status.text.startswith("#memo")):
            # DBのパスを生成
            dbpath = "DB/{}.db".format(status.user.id)
            # ID生成
            memo = {}
            memo["id"] = status.id
            # Tweetが引用ツイートかどうか
            if hasattr(status, "quoted_status"):
                status = status.quoted_status
            # データ書き込み
            memo["contents"] = status.text[6:]
            try:
                memo["media"] = status.entities["media"][0]["media_url"]
            except:
                memo["media"] = "null"
            memo["tweet_url"] = "https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str
            memo["time"] = str(status.created_at)
            db.write_memo(dbpath, memo)
            # リプを送信
            self.api.update_status("@{} メモに登録しました[{}]".format(status.user.screen_name,memo["time"]), status.id)

    def on_direct_message(self, status):
        """DMの処理"""
        status = status.direct_message
        # DBのパスを生成
        dbpath = "DB/{}.db".format(status["sender_id"])
        # データ書き込み
        memo = {}
        memo["id"] = status["id"]
        memo["contents"] = status["text"]
        try:
            memo["media"] = status["entities"]["media"][0]["media_url"]
        except:
            memo["media"] = "null"
        memo["tweet_url"] = "DirectMessage"
        memo["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.write_memo(dbpath, memo)
        # リプを送信
        self.api.send_direct_message(status["sender_id"], text="メモに登録しました[{}]".format(memo["time"]))
    
    def on_event(self, event):
        """フォロバ"""
        if event.event == 'follow':
            if self.me.id != event.source["id"] and event.target["id"] == self.me.id:
                self.api.create_friendship(event.source["id"])

if __name__ == '__main__':
    setting = json.load(open("setting.json"))
    auth = get_oauth(setting)
    stream = tp.Stream(auth, StreamListener(tp.API(auth)), secure=True)
    print("start")
    stream.userstream()

class TLThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
 
    def run(self):
        setting = json.load(open("setting.json"))
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