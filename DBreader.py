import os
import sqlite3 as sql
import requests
import json

# DBに書き込み
def write_memo(path, memo):
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        conn = sql.connect(path)
        conn.execute("""create table list (id integer, contents text, media text,
                        source text, time text)""")
        conn.commit()
    SQL = "insert into list values(?,?,?,?,?)"
    value = (memo["id"], memo["contents"], memo["media"], memo["source"], memo["time"])
    conn.execute(SQL, value)
    conn.commit()
    conn.close()

# DBから削除
def del_memo(path, id):
    if os.path.exists(path):
        conn = sql.connect(path)
    else:
        raise ValueError
    conn.execute("delete from list where id = {}".format(id))
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
        memolist.append({"id":row["id"], "contents":row["contents"], "time":row["time"]})
    cur.close()
    conn.close()
    return memolist

# DBから詳細情報取得
def get_detail(id, dbfile):
    if os.path.exists(dbfile):
        conn = sql.connect(dbfile)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute("select * from list where id = {}".format(id))
    row = cur.fetchone()
    detail = {
        "id":row["id"],
        "contents":row["contents"],
        "media":row["media"],
        "source":row["source"],
        "time":row["time"]
    }
    cur.close()
    conn.close()
    return detail

# DBから検索
def search_db(mode, target, dbfile):
    images = []
    if os.path.exists(dbfile):
        conn = sql.connect(dbfile)
    else:
        raise ValueError
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute("select count(filename) from {} where username like '%{}%'".format(table,userid))
    count = cur.fetchone()[0]
    cur.execute( "select * from {} where username like '%{}%'".format(table,userid) )
    for row in cur:
        images.append({"id":int(row["filename"]), "tags":row["tags"][1:-1], "image":row["image"]})
    cur.close()
    conn.close()
    return memolist

# 埋め込み用HTMLの取得
def get_html(url):
    try:
        r = requests.get("https://publish.twitter.com/oembed", {"url":url})
        data = json.loads(r.text)
        return data["html"]
    except:
        raise
