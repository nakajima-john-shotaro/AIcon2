// ウィンドウに関しての関数です
$(window).on('load resize', function () {
    var windowWidth = window.innerWidth;
    var elements = $('#fixed-area');
    if (windowWidth >= 768) {
        Stickyfill.add(elements);
    } else {
        Stickyfill.remove(elements);
    }
});

$(window).load(function () {
    change_advanced_param(model_button_id, param_button_id);
    $('html,body').animate({ scrollTop: 0 }, '1');
});

$('#reload').on('click', function () {
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
$('#DeepDaze').addClass('add_Color');
var model_button_id = 'DeepDaze';
$('.Model_Area').click(function() {
    if (!communicate_status){
        model_button_id = this.id;
        $('.Model_Area').removeClass('add_Color');
        $('#' + model_button_id).addClass('add_Color');
        change_advanced_param(model_button_id, param_button_id);
    };
});


$('.Model_Area').click(function () {
    if (!communicate_status) {
        let img_id_list = [];
        $(".carousel-item").each(function () {
            img_id_list.push('#' + $(this).attr('id'));
        });
        if (model_button_id === 'DeepDaze') {
            for (let i = 0; i < img_id_list.length; i++) {
                $(img_id_list[i]).attr('src', "https://lorempixel.com/250/250/cats/" + (i + 1));
            };
        }
        else if (model_button_id === 'BigSleep') {
            for (let i = 0; i < img_id_list.length; i++) {
                $(img_id_list[i]).attr('src', "https://lorempixel.com/250/250/sports/" + (i + 1));
            };
        }
    }
});


// 仕上がりの調整に関するボタンです
$('#middle').addClass('add_Color');
var param_button_id = 'middle';
$('.set_param_button').click(function () {
    if (!communicate_status) {
        param_button_id = this.id;
        $('.set_param_button').removeClass('add_Color');
        $('#' + param_button_id).addClass('add_Color');
        change_advanced_param(model_button_id, param_button_id);
    }
});

var backbone_model = "RN50x4";
function change_advanced_param(model_button_id , param_button_id) {
    let setting_param_key = Object.keys(MODEL_PARAM[model_button_id][param_button_id])
    $('.advanced_params').fadeOut(0)
    if (model_button_id === 'DeepDaze'){
        for (let i = 0; i < setting_param_key.length; i++) {
            $('#' + setting_param_key[i]).fadeIn(400);
        };
        $('#iter_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["iter"]);
        $('#num_layer_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["num_layer"]);
        $('#hidden_size_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["hidden_size"]);
        $('#batchsize_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["batch_size"]);
        $('#gae_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["gae"]);
        $('.backbone_button').removeClass('add_Color');
        $('#' + MODEL_PARAM[model_button_id][param_button_id]["backbone"]).addClass('add_Color');
        backbone_model = MODEL_PARAM[model_button_id][param_button_id]["backbone"];
    }
    else if (model_button_id === 'BigSleep'){
        for (let i = 0; i < setting_param_key.length; i++) {
            $('#' + setting_param_key[i]).fadeIn(400);
        };
        $('#iter_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["iter"]);
        $('#gae_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["gae"]);
        $('.backbone_button').removeClass('add_Color');
        $('#' + MODEL_PARAM[model_button_id][param_button_id]["backbone"]).addClass('add_Color');
        backbone_model = MODEL_PARAM[model_button_id][param_button_id]["backbone"];
    }
};


// 詳細設定に関しての関数です 
// スライダーに関する関数です
function get_slider_values() {
    let slider_val_dict = {};
    slider_val_dict["iter"] = document.getElementById("iter_slider").value;
    slider_val_dict["num_layer"] = document.getElementById("num_layer_slider").value;
    slider_val_dict["hidden_size"] = document.getElementById("hidden_size_slider").value;
    slider_val_dict["batch_size"] = document.getElementById("batch_size_slider").value;
    slider_val_dict["gae"] = document.getElementById("gae_slider").value;
    return slider_val_dict;
}

// バックボーンに関するボタンです
$('#ResNet50').addClass('add_Color');
var backbone = 'ResNet50';
$('.backbone_button').click(function () {
    if (!communicate_status) {
    backbone = this.id;
    $('.backbone_button').removeClass('add_Color');
    $('#' + backbone).addClass('add_Color');
    }
});

// 入力する文に関しての関数です
var text_length = 0;
$('#textarea').on('input', function () {
    text_length = $('#textarea').val().length;
    check()
});

// 画像のドラッグ＆ドロップに関する関数です
$(function () {
    
        // クリックで画像を選択する場合
        $('#drop_area').on('click', function () {
            if (!communicate_status) {
                $('#input_file').click();
            }
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
});

// ドラッグしている要素がドロップ領域に入ったとき・領域にある間
$('#drop_area').on('dragenter dragover', function (event) {
    if (!communicate_status) {
        event.stopPropagation();
        event.preventDefault();
        $('#drop_area').css('border', '5px solid #333');  // 枠を実線にする
    }
});

// ドラッグしている要素がドロップ領域から外れたとき
$('#drop_area').on('dragleave', function (event) {
    if (!communicate_status) {
        event.stopPropagation();
        event.preventDefault();
        $('#drop_area').css('border', '5px dashed #ccc');  // 枠を点線に戻す
    }
});

// ドラッグしている要素がドロップされたとき
$('#drop_area').on('drop', function (event) {
    if (!communicate_status) {
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
    if (!file.type.match(imageType)) {
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
    reader.readAsDataURL(file); // ファイル読み込みを非同期でバックグラウンドで開始
}

$(window).resize(function () {
    
    $('#upload_img').width($('#drop_area').outerWidth());
    $('#upload_img').height($('#drop_area').outerHeight());
});

// アイコン画像を消去するボタン
$('#img_delete_button').on('click', function () {
    if (!communicate_status) {
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
function check() {
    let text_length_status = (text_length > 0 ? true : false);
    let start_status = text_length_status;
    if (start_status) {
        $('#start_quit_button').removeClass('disabled');
    }
    else {
        $('#start_quit_button').addClass('disabled');
    }
};

// 開始後に関する関数です
function stop_input() {
    let advanced_param_list = Object.keys(MODEL_PARAM[model_button_id][param_button_id])
    for (let i = 0; i < advanced_param_list.length; i++) {
        console.log( advanced_param_list[i])
        $('#' + advanced_param_list[i] + '_slider').prop('disabled', true);
    };
    // $('#').prop('disabled', true);
    $('#textarea').prop('disabled', true);
    $('#start_quit_button').addClass('red accent-2')
    $('#start_quit_icon').text('cancel');
    $('#start_quit_text').text('Quit');
}

// 中止ボタンを押された際に送信データを変更する
function abort_signal() {
    send_data = {
        model_name: model_button_id,
        text: $('#textarea').val(),
        total_iter: parseInt(get_range_value()),
        size: 256,
        hash: hash,
        abort: true,
    };
    console.log('中止信号が押されました')
    let send_json_data = JSON.stringify(send_data)
    communicate(send_json_data)
};

var communicate_status = false;
var hash = '00000000-0000-0000-0000-000000000000';
function start() {
    console.log("start直下")
    stop_input()
    communicate_status = true;

    $('#start_quit_button').attr("onclick", "abort_signal()")
    $('#img_make_container').fadeIn('1000');
    const target = $('#img_make_container').get(0).offsetTop;
    $('body,html').animate({ scrollTop: target }, 500, 'swing');
    
    // スライダーの値を取得
    const slider_vals = get_slider_values();
 
    console.log(slider_vals);
    // 送信するデータ
    send_data = {
        model_name: model_button_id,
        text: $('#textarea').val(),
        total_iter: parseInt(slider_vals['iter']),
        num_layer: parseInt(slider_vals['num_layer']),
        hidden_size: parseInt(slider_vals['hidden_size']),
        batch_size: parseInt(slider_vals['batch_size']),
        gae: parseInt(slider_vals['gae']),
        backbone: backbone_model,
        size: 256,
        hash: hash,
        abort: false,

    };
    let send_json_data = JSON.stringify(send_data)
    console.log('s_data')
    console.log(send_data)
    communicate(send_json_data)
};

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
            console.log("r_data");
            console.log(r_data);
            console.log("s_data");
            console.log(s_data);
            tmp_data = JSON.parse(s_data);

            $('#result_img').attr("src", r_data["img_path"]).on("load", function () {
                $('#result_img').fadeIn();
            });
            // 通信継続の確認
            if (!r_data["complete"]) {
                wait(300).done(function () {
                    tmp_data["hash"] = r_data["hash"];
                    hash = r_data["hash"];
                    communicate(JSON.stringify(tmp_data));
                });
            } else {
                console.log("Communication is finished")
                PushNotification()
            }
        })
        .fail(function (r_data, textStatus, error) {
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