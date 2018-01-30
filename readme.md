## メモ
### DBカラム
- id:integer:status.id
- title:text:status.text[:20]  
- contents:text:status.text  
- media:text:status.entities["media"]  
- url:text:status.entites["url"]  
- source:text:"https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str  
- time:text(YYYY-MM-DD HH:MM:SS):created_at  
- remind:text(YYYY-MM-DD):""
- reserve:text:""  

mediaは,区切り、urlは|区切り

### 使ってるやつ  
Python 3.5  
Flask  
Tweepy  
Bootstrap 4  
Open Iconic  
https://github.com/sindresorhus/github-markdown-css  
https://github.com/matthiasmullie/jquery-autoexpand  
https://github.com/uxsolutions/bootstrap-datepicker  
https://github.com/pekko1215/Nobeer