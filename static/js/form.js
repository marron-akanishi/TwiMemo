var label_change = function(){
    var id = $(this).attr('id');
    $(`label[for=${id}]`).text($(this).val().split('\\').pop());
};

$(() => {
    $('textarea').autoExpand();
    var image_beer = $('#images').Nobeer({
        idx: media_idx,
        domList: [
            "#media"
        ],
        show: function () {
            this.slideDown();
        },
        hide: function (del) {
            this.slideUp(del);
        },
        pipe: function (i) {
            this.find('input').attr('value', '');
        }
    })
    var url_beer = $('#urls').Nobeer({
        idx: url_idx,
        domList: [
            "#url"
        ],
        show: function () {
            this.slideDown();
        },
        hide: function (del) {
            this.slideUp(del);
        },
        pipe: function (i) {
            this.find('input').attr('value', '');
        }
    })
    var file_beer = $('#files').Nobeer({
        idx: url_idx,
        max: 4,
        domList: [
            "#file"
        ],
        show: function () {
            this.slideDown();
        },
        hide: function (del) {
            this.slideUp(del);
        },
        pipe: function (i) {
            this.find('input').attr('id', 'media_'+i);
            this.find('input').on('change', label_change);
            this.find('label').attr('for', 'media_' + i);
        }
    })
    $('#imageadd').click(image_beer.add);
    $('#imageremove').click(image_beer.remove);
    $('#urladd').click(url_beer.add);
    $('#urlremove').click(url_beer.remove);
    $('#fileadd').click(file_beer.add);
    $('#fileremove').click(file_beer.remove);
    $('#media_0').on('change', label_change);
    $('#edit-form').submit(function () {
        var medias = $(".media-input").map(function () {
            return $(this).val();
        }).get().join(',');
        console.log(medias)
        $('<input>').attr({
            'type': 'hidden',
            'name': 'media',
            'value': medias
        }).appendTo(this);
        var urls = $(".url-input").map(function () {
            return $(this).val();
        }).get().join('|');
        $('<input>').attr({
            'type': 'hidden',
            'name': 'url',
            'value': urls
        }).appendTo(this);
        return true;
    });
    $('#new-form').submit(function(){
        var that = this
        var medias = $(".media-input");
        $('<input>').attr({
            'type': 'hidden',
            'name': 'count',
            'value': medias.length
        }).appendTo(that);
        medias.each(function(){
            $(this).attr("name", $(this).attr('id')).appendTo(that);
        });

        var urls = $(".url-input").map(function () {
            return $(this).val();
        }).get().join('|');
        $('<input>').attr({
            'type': 'hidden',
            'name': 'url',
            'value': urls
        }).appendTo(that);
        return true;
    });
});