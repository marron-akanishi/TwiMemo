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
                location.href = "/list";
            },
            error: function(error) {
                alert('削除に失敗しました');
                $(".btn").attr('disabled', false);
            }
        });
    }
}

$(()=>{
    $('#datepicker .in-line').datepicker({
        format: "yyyy-mm-dd",
        language: "ja"
    });
    $('#datepicker .in-line').on('changeDate', function () {
        $('#date').attr('value', $(this).datepicker('getFormattedDate'))
    });
    $('#remind-setting').on('show.bs.modal', function (event) {
        var today = new Date();
        today = today.getFullYear() + "-" + today.getMonth() + 1 + "-" + today.getDate();
        var recipient = $(event.relatedTarget).data('memoid') // Extract info from data-* attributes
        $('#memoid').attr('value', recipient)
        $('#date').attr('value', today)
        
    });
})