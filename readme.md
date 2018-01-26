## メモ
### DB
- id:integer:status.id
- title:text:status.text[:20]  
- contents:text:status.text  
- media:text:status.entities["media"]  
- url:text:status.entites["url"]  
- source:text:"https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str  
- time:text(YYYY-MM-DD HH:MM:SS):created_at  
- remind:text(YYYY-MM-DD):""
- reserve:text:""

### 使ってるやつ  
https://github.com/pekko1215/Nobeer