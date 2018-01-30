import sqlite3 as sql
import db_utils as db

filelist = ["./DB/0.db.org", "./DB/1.db.org"]

for filename in filelist:
    memolist = []
    conn = sql.connect(filename)
    conn.row_factory = sql.Row
    cur = conn.cursor()
    cur.execute( "select * from list order by time desc" )
    for row in cur:
        memolist.append({
            "id":row["id"],
            "contents":row["contents"],
            "media":row["media"],
            "url":row['url'],
            "source":row['source'],
            "time":row["time"]
        })
    cur.close()
    conn.close()
    for memo in memolist:
        if len(memo["contents"]) >= 20:
            memo["title"] = memo["contents"][:20] + "..."
        else:
            memo["title"] = memo["contents"]
        if memo["media"] == "null":
            memo["media"] = ""
        if memo["url"] == "null":
            memo["url"] = ""
        db.write_memo(filename.replace(".org",""), memo)