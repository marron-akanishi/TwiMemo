function delmemo(id){
    if(confirm("削除します\nよろしいですか？")){
        $.ajax({
            url: '/delete/'+id,
            type: 'DELETE',
            beforeSend: function(xhr, settings) {
                // ボタンを無効化し、二重送信を防止
                $(".btn").attr('disabled', true);
            },
            success:function(resultdata) {
                alert('削除しました');
                location.href = "/list";
            },
            error: function(error) {
                alert('削除に失敗しました');
                $(".btn").attr('disabled', false);
            }
        });
    }
}