// ウィンドウに関しての関数です
$(window).on('load resize', function() {
    var windowWidth = window.innerWidth;
    var elements = $('#fixed-area');
    if (windowWidth >= 768) {
    Stickyfill.add(elements);
    }else{
    Stickyfill.remove(elements);
    }
});

$(window).load(function(){
	$('html,body').animate({ scrollTop: 0 }, '1');
});

$('#reload').on('click',function(){
    location.reload();
	$('html,body').animate({ scrollTop: 0 }, '1');
});

// キー入力に関係する関数です
$(function () {
    $('.cancelEnter')
        .on('keydown', function (e) {
            if (e.key == 'Enter') {
                return false;
            }
        })
});

// モデルの選択に関する関数です
// materializeが原因で脳筋手法に出ます
// 今後はもっと汎用性のあるものを作ります…
var DeepDaze_button_active = false;
var BigSleep_button_active = false;
$("#DeepDaze").click(function(){
    if (!communicate_status){
        if (!(DeepDaze_button_active ^ BigSleep_button_active)){
            document.getElementById("DeepDaze").classList.add("add_Color");
            document.getElementById("BigSleep").classList.remove("add_Color");
            DeepDaze_button_active = true;
            BigSleep_button_active = false;
        }
        else if (DeepDaze_button_active ^ BigSleep_button_active){
            if (DeepDaze_button_active) {
                document.getElementById("DeepDaze").classList.remove("add_Color");
            DeepDaze_button_active = false;
            BigSleep_button_active = false;
            }
            else if (BigSleep_button_active) {
            document.getElementById("DeepDaze").classList.add("add_Color");
            document.getElementById("BigSleep").classList.remove("add_Color");
            DeepDaze_button_active = true;
            BigSleep_button_active = false;
            }
        }
    }
});

$("#BigSleep").click(function(){
    if (!communicate_status){
        if (!(DeepDaze_button_active ^ BigSleep_button_active)){
            document.getElementById("BigSleep").classList.add("add_Color");
            document.getElementById("DeepDaze").classList.remove("add_Color");
            DeepDaze_button_active = false;
            BigSleep_button_active = true;
        }
        else if (DeepDaze_button_active ^ BigSleep_button_active){
            if (BigSleep_button_active) {
                document.getElementById("BigSleep").classList.remove("add_Color");
                DeepDaze_button_active = false;
                BigSleep_button_active = false;
            }
            else if (DeepDaze_button_active) {
                document.getElementById("BigSleep").classList.add("add_Color");
                document.getElementById("DeepDaze").classList.remove("add_Color");
                DeepDaze_button_active = false;
                BigSleep_button_active = true;
            }
        }
    }
});


$('.Model_Area').click( function() {
    let img_id_list = [];
    $(".carousel-item").each(function() {
        img_id_list.push('#'+$(this).attr('id'));
    });

    if (DeepDaze_button_active) {
        for (let i = 0; i < img_id_list.length; i++){
            $(img_id_list[i]).attr('src',"https://lorempixel.com/250/250/nature/" + (i+1));
        };
    }
    else if (BigSleep_button_active) {
        for (let i = 0; i < img_id_list.length; i++){
            $(img_id_list[i]).attr('src',"https://lorempixel.com/250/250/sports/" + (i+1));
        };
    }
    else {
        for (let i = 0; i < img_id_list.length; i++){
            $(img_id_list[i]).attr('src', "https://lorempixel.com/250/250/cats/" + (i+1));
        };
    }
    check()
});


// 仕上がりの調整に関するボタンです
$('#set_param_middle').addClass('add_Color');
var param_button_id = 'set_param_middle';
$('.set_param_button').click( function() {
    param_button_id = this.id;
    $('.set_param_button').removeClass('add_Color');
    $('#'+param_button_id).addClass('add_Color');
});



// スライダーに関する関数です
function get_range_value() {
    const slider = document.getElementById("slider")
    return slider.value;
};

// 入力する文に関しての関数です
var text_length = 0;
$('#textarea').on('input', function() {
    text_length = $('#textarea').val().length;
    check()
});

// 画像のドラッグ＆ドロップに関する関数です
$(function () {
    if (!communicate_status){
        // クリックで画像を選択する場合
        $('#drop_area').on('click', function () {
            $('#input_file').click();
        });

        $('#input_file').on('change', function () {
        // 画像が複数選択されていた場合
        if (this.files.length > 1) {
            alert('アップロードできる画像は1つだけです');
            $('#input_file').val('');
            return;
        }
        handleFiles(this.files);
        });
    }
});

// ドラッグしている要素がドロップ領域に入ったとき・領域にある間
$('#drop_area').on('dragenter dragover', function (event) {
    event.stopPropagation();
    event.preventDefault();
    $('#drop_area').css('border', '5px solid #333');  // 枠を実線にする
});

// ドラッグしている要素がドロップ領域から外れたとき
$('#drop_area').on('dragleave', function (event) {
    event.stopPropagation();
    event.preventDefault();
    $('#drop_area').css('border', '5px dashed #ccc');  // 枠を点線に戻す
});

// ドラッグしている要素がドロップされたとき
$('#drop_area').on('drop', function (event) {
    if (!communicate_status){
        event.preventDefault();
        $('#input_file')[0].files = event.originalEvent.dataTransfer.files;
        // 画像が複数選択されていた場合
        if ($('#input_file')[0].files.length > 1) {
            alert('アップロードできる画像は1つだけです');
            $('#input_file').val('');
            return;
        }
        handleFiles($('#input_file')[0].files);
    }
});

// 選択された画像ファイルの操作
function handleFiles(files) {
    var file = files[0];
    var imageType = 'image.*';

    // ファイルが画像が確認する
    if (! file.type.match(imageType)) {
        alert('画像ファイルではありません。\n画像を選択してください');
        $('#input_file').val('');
        $('#drop_area').css('border', '5px dashed #ccc');
        return;
    }

    $('#drop_area').hide();  // いちばん上のdrop_areaを非表示にします
    $('#img_delete_button').show(); 

    let img = document.createElement('img');  // <img>をつくります
    img.id = 'upload_img';
    img.width = $('#drop_area').outerWidth();
    img.height = $('#drop_area').outerHeight();
    let reader = new FileReader();
    reader.onload = function () {  // 読み込みが完了したら
        img.src = reader.result;  // readAsDataURLの読み込み結果がresult
        $('#preview_field').append(img);  // preview_filedに画像を表示
    }
    console.log($('#drop_area').attr('width'))
    reader.readAsDataURL(file); // ファイル読み込みを非同期でバックグラウンドで開始
}

$(window).resize(function() {
    $('#upload_img').width($('#drop_area').outerWidth());
    $('#upload_img').height($('#drop_area').outerHeight());
});

// アイコン画像を消去するボタン
$('#img_delete_button').on('click', function () {
    if (!communicate_status){
        $('#preview_field').empty();  // 表示していた画像を消去
        $('#input_file').val('');  // inputの中身を消去
        $('#drop_area').show();  // drop_areaをいちばん前面に表示
        $('#img_delete_button').hide();  // clear_buttonを非表示
        $('#drop_area').css('border', '5px dashed #aaa');  // 枠を点線に変更
    }
});

// drop_area以外でファイルがドロップされた場合、ファイルが開いてしまうのを防ぐ
$(document).on('dragenter', function (event) {
    event.stopPropagation();
    event.preventDefault();
});
$(document).on('dragover', function (event) {
    event.stopPropagation();
    event.preventDefault();
});
$(document).on('drop', function (event) {
    event.stopPropagation();
    event.preventDefault();
});


// 選択の確認
function select_check() {
    let use_model = "";
    if (DeepDaze_button_active === true) {
        use_model = "DeepDaze";
    }
    else if (BigSleep_button_active === true) {
        use_model = "BigSleep";
    }
    return use_model;
}

function check() {
    let model_button_status = DeepDaze_button_active || BigSleep_button_active;
    let text_length_status = (text_length > 0 ? true : false);
    let start_status = model_button_status && text_length_status;
    if (start_status) {
        $('#start_quit_button').removeClass('disabled');
    }
    else {
        $('#start_quit_button').addClass('disabled');
    }
};

// 開始後に関する関数です
function stop_input(){
    $('#slider').prop('disabled', true);
    $('#textarea').prop('disabled', true);
    $('#start_quit_button').addClass('red accent-2')
    $('#start_quit_icon').text('cancel');
    $('#start_quit_text').text('Quit');
}


var communicate_status = false;
function start() {
    PushNotification()
    let abort_signal = ($('#start_quit_text').text() === 'Play' ? false : true);
    communicate_status = true;
    stop_input()
    // 使用するモデルの選択
    const use_model = select_check();
    if (use_model === "") {
        return;
    }

    $('#img_make_container').fadeIn(1000);
    const target = $('#img_make_container').get(0).offsetTop;
    $('body,html').animate({scrollTop:target}, 500, 'swing');
    // スライダーの値を取得
    const slider_val = get_range_value()

    // 入力された文字を取得
    var input_text = $('#textarea').val();

    // 送信するデータ
    send_data = {
        model_name : use_model,
        text : input_text,
        total_iter : parseInt(slider_val),
        size : 256,
        hash : '00000000-0000-0000-0000-000000000000',
        abort : abort_signal,

    };
    let send_json_data = JSON.stringify(send_data)
    // communicate(send_json_data)
}

// 通信に関しての関数
function communicate(s_data) {
    $.ajax({
        url: "http://localhost:5050/service",
        method: "POST",
        data: s_data,
        dataType: "json", //データの受信形式
        timeout: 10000,
        async: false, //同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
        .done(function (r_data, textStatus, xhr) {
            console.log("Communication success");
            // console.log(r_data);
            console.log(s_data);
            const tmp_data = JSON.parse(s_data);

            $('#result_img').attr("src", r_data["img_path"]).on("load", function (){
                $('#result_img').fadeIn();
            });
            // 通信継続の確認
            if (!r_data["complete"] ) {
                wait(3000).done(function () {
                    tmp_data["hash"] = r_data["hash"];
                    communicate(JSON.stringify(tmp_data));
                });
            }else{
                console.log("Communication is finished")
            }
        })
        .fail(function (r_data, textStatus, error){ 
            console.log("Commnucation error");
            console.log(r_data);
            console.log(typeof r_data);
        });
}

function wait(msec) {
    var objDef = new $.Deferred();
    setTimeout(function () {
        objDef.resolve(msec);
    }, msec);
    return objDef.promise();
}


// 通知に関しての関数
function PushNotification() {
    Push.create('AIconです。', {
    body: '画像を作り終えました！！',
    icon: 'https://lorempixel.com/250/250/cats/0',
    timeout: 5000,
    onClick: function () {
    this.close();
    location.href = 'https://www.yahoo.co.jp';
    }
    });
}