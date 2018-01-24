import os
import sqlite3 as sql
import requests
import json

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
        memolist.append({
            "id":row["id"],
            "title":row["title"],
            "media":row["media"],
            "url":row['url'],
            "time":row["time"]
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
    cur.execute("select * from list where id = {}".format(id))
    row = cur.fetchone()
    detail = {
        "id":row["id"],
        "title":row["title"],
        "contents":row["contents"],
        "media":row["media"].split(","),
        "url":row["url"],
        "source":row["source"],
        "time":row["time"]
    }
    cur.close()
    conn.close()
    return detail

# DBから検索
def search_memo(path):
    images = []
    if os.path.exists(path):
        conn = sql.connect(path)
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