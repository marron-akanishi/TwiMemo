function delmemo(id){
    return;
    $.ajax({
        url: '/delete/'+id,
        type: 'DELETE',
        beforeSend: function(xhr, settings) {
            // ボタンを無効化し、二重送信を防止
            $(".btn").attr('disabled', true);
        },
        success:function(resultdata) {
            alert('削除しました');
        },
        error: function(error) {
            alert('削除に失敗しました');
        },
        complete : function(data) {
            // Loadingイメージを消す
            $(".btn").attr('disabled', false);
        }
    });
}