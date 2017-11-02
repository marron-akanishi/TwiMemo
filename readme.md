## DB
id:integer:status.id  
contents:text:status.text  
media:text:status.entities  
tweet_url:text:"https://twitter.com/" + status.user.screen_name + "/status/" + status.id_str  
time:text(YYYY-MM-DD HH:MM:SS):created_at  
timeに関しては編集された場合はその時間に更新  