import os
import sqlite3 as sql
import requests
import json

setting = json.load(open("setting.json"))

# DBに書き込み
def write_memo(path, memo):
    temp = []
    for media in memo["media"].split(','):
        if media.startswith("http"):
            temp.append(media)
    memo["media"] = ','.join(temp)
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        conn = sql.connect(path)
        conn.execute("""create table list (id integer, title text, contents text, media text,
                        url text, source text, time text, remind text,  reserve text)""")
        conn.commit()
    SQL = "insert into list values(?,?,?,?,?,?,?,?,?)"
    value = (memo["id"], memo["title"], memo["contents"], memo["media"], memo['url'], memo["source"], memo["time"], "", "")
    conn.execute(SQL, value)
    conn.commit()
    conn.close()

# DBから削除
def del_memo(path, id):
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute("select * from list where id = ?",(id,))
    row = cur.fetchone()
    media = row["media"].split(",")
    cur.close()
    for url in media:
        if setting["UploadServer"] in url:
            try:
                os.remove(setting["UploadDir"] + "/" + url.split('/')[-1])
            except:
                continue
    conn.execute("delete from list where id = ?",(id,))
    conn.commit()
    conn.close()

# DB更新
def update_memo(path, id, memo):
    del_memo(path, id)
    write_memo(path, memo)

# DBからリスト取得
def get_list(path):
    memolist = []
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute( "select * from list order by time desc" )
    for row in cur:
        memolist.append({
            "id":row["id"],
            "title":row["title"],
            "media":row["media"],
            "url":row['url'],
            "time":row["time"],
            "remind":row["remind"]
        })
    cur.close()
    conn.close()
    return memolist

# DBから詳細情報取得
def get_detail(path, id):
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute("select * from list where id = ?",(id,))
    row = cur.fetchone()
    detail = {
        "id":row["id"],
        "title":row["title"],
        "contents":row["contents"],
        "media":row["media"].split(","),
        "url":row["url"].split("|"),
        "source":row["source"],
        "time":row["time"]
    }
    cur.close()
    conn.close()
    return detail

# DBから検索
def search_list(path, search):
    memolist = []
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute("select * from list where contents like ? escape '$' order by time desc",("%"+search+"%",))
    for row in cur:
        memolist.append({
            "id":row["id"],
            "title":row["title"],
            "media":row["media"],
            "url":row['url'],
            "time":row["time"],
            "remind":row["remind"]
        })
    cur.close()
    conn.close()
    return memolist