var ICON_VARSION = '1.2.1';
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
    $('#textarea').focus();
    $('#communication_partner').val($.cookie('url'));
    if ($('#communication_partner').val() == ''){
        $('#communication_partner').val('localhost');
    }
    $('html,body').animate({ scrollTop: 0 }, '1');
    send_data = {
        version: ICON_VARSION
    };
    let check_version_data = JSON.stringify(send_data); 
    $.ajax({
        url: "http://" + $('#communication_partner').val() + ":5050/test",
        method: "POST",
        data: check_version_data,
        dataType: "json",
        timeout: 10000,
        async: true, // 同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
        .done(function (r_data) {
            communication_status = true;
            if (!$.cookie('first_login')) {
                if (r_data['pre_diagnostics'] !== 0){
                    let pre_check_list = test_device_status(r_data['pre_diagnostics']);
                    let notice_sting = "Something went wrong.\n" + pre_check_list[0];
                    notify_alert("Oops!", notice_sting, false, pre_check_list[1]);
                }
                $.cookie('first_login', 'no');
            }
        })
        .fail(function () {
            communication_status = false;
            notify_alert("サーバに接続できません", "Server IP Addressを確認してください。", false);
        });

});

$('#reload').on('click', function () {
    location.reload();
    $('html,body').animate({ scrollTop: 0 }, '1');
});

$('#nico_font').on('click', function () {
    location.reload();
    $('html,body').animate({ scrollTop: 0 }, '1');
});


// helpが押されたときに関する関数です
$('#help').click(function() {
    $.ajax({
        url: "http://" + $('#communication_partner').val() + ":5050/help",
        method: "GET",
        timeout: 10000,
        async: false, //同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
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

var DeepDaze_dir = [
    '../static/demo_img/DeepDaze/Women_in_cyberpunk.png',
    '../static/demo_img/DeepDaze/inferno.png',
    '../static/demo_img/DeepDaze/burning_ice.png',
    '../static/demo_img/DeepDaze/Catcher_in_the_Rye.png',
    '../static/demo_img/DeepDaze/cosmos.png',
    '../static/demo_img/DeepDaze/New_green_promenade.png'
];

var BigSleep_dir = [
    '../static/demo_img/BigSleep/Alice_in_wonderland.png',
    '../static/demo_img/BigSleep/Demon_Slayer.png',
    '../static/demo_img/BigSleep/Fantasia_World.png',
    '../static/demo_img/BigSleep/Fantasia_galaxy.png',
    '../static/demo_img/BigSleep/bread.png',
    '../static/demo_img/BigSleep/cinderella.png',
    '../static/demo_img/BigSleep/fire_and_ice.png',
    '../static/demo_img/BigSleep/galaxy.png',
    '../static/demo_img/BigSleep/lagoon.png'
];

var random = 0;
$('.Model_Area').click(function () {
    if (!communicate_status) {
        let img_id_list = [];
        $(".carousel-item").each(function () {
            img_id_list.push('#' + $(this).attr('id'));
        });
        if (model_button_id === 'DeepDaze') {
            for (let i = 0; i < img_id_list.length; i++) {
                random = Math.floor(Math.random() * (DeepDaze_dir.length + 1 ));
                $(img_id_list[i]).attr('src', DeepDaze_dir[random]);
                $('.set_size_button').removeClass('add_Color');
                $('#size_256').addClass('add_Color');
                img_size = '256';
            };
        }
        else if (model_button_id === 'BigSleep') {
            for (let i = 0; i < img_id_list.length; i++) {
                random = Math.floor(Math.random() * (BigSleep_dir.length + 1 ));
                $(img_id_list[i]).attr('src', BigSleep_dir[random]);
                $('.set_size_button').removeClass('add_Color');
                $('#size_512').addClass('add_Color');
                img_size = '512';
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
        $('#seed').fadeIn(400);
        $('#source_img').fadeIn(400);
        $('#target_img').fadeIn(400);
        $('#iter_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["iter"]);
        $('#num_layer_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["num_layer"]);
        $('#hidden_size_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["hidden_size"]);
        $('#batch_size_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["batch_size"]);
        $('#gae_slider').prop('value', MODEL_PARAM[model_button_id][param_button_id]["gae"]);
        $('.backbone_button').removeClass('add_Color');
        $('#' + MODEL_PARAM[model_button_id][param_button_id]["backbone"]).addClass('add_Color');
        backbone_model = MODEL_PARAM[model_button_id][param_button_id]["backbone"];
    }
    else if (model_button_id === 'BigSleep'){
        for (let i = 0; i < setting_param_key.length; i++) {
            $('#' + setting_param_key[i]).fadeIn(400);
        };
        $('#seed').fadeIn(400);
        $('#carrot').fadeIn(400);
        $('#stick').fadeIn(400);
        $('#source_img').fadeIn(400);
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
$('.backbone_button').click(function() {
    if (!communicate_status) {
    backbone_model = this.id;
    backbone = this.id;
    $('.backbone_button').removeClass('add_Color');
    $('#' + backbone).addClass('add_Color');
    }
});


// seedのボタンに関する関数です
var seed_buttun_status = 'random';
$(function (){
    $('#seed_button_specify').on('click', function() {
        if (!communicate_status) {
            $('#seed_value').prop('disabled', false);
            $('#seed_value').focus();
            seed_buttun_status = 'specify';
        }
    })
    $('#seed_button_random').on('click', function() {
        if (!communicate_status) {
            $('#seed_value').prop('disabled', true);
            $('#seed_value').prop('value', null);
            seed_buttun_status = 'random';
        }
    })
});

function get_seed_value() {
    let seed_value = null;
    if (seed_buttun_status === 'random') {
        seed_value = null;
    } 
    else if (seed_buttun_status === 'specify') {
        if ($('#seed_value').prop('value') === '') {
            seed_value = null;
        }
        else {
            seed_value = $('#seed_value').prop('value');
        }
    }
    return seed_value;
};


// 画像のドラッグ＆ドロップに関する関数です
// source
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
            notify_alert('ファイルが多すぎます', 'アップロードできる画像は1つだけです。', false);
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
            notify_alert('ファイルが多すぎます', 'アップロードできる画像は1つだけです。', false);
            $('#input_file').val('');
            $('#drop_area').css('border', '5px dashed #ccc');  // 枠を点線に戻す
            return;
        }
        handleFiles($('#input_file')[0].files);
    }
});

// 選択された画像ファイルの操作
var source_img = null;
var file = null;
function handleFiles(files) {
    file = files[0];
    var imageType = 'image.*';
    // ファイルが画像が確認する
    if (!file.type.match(imageType)) {
        notify_alert('非対応のファイルです', '画像を入れてください。', false);
        $('#input_file').val('');
        $('#drop_area').css('border', '5px dashed #ccc');
        return;
    }
    $('#drop_area').hide();
    $('#img_delete_button').show();
    const resize_width = 512;
    const resize_height = 512;
    let image = new Image();
    let source_reader = new FileReader();
    source_reader.onload = function(e) {
        image.onload = function() {
            var canvas = $('#canvas_src').attr('width', resize_width).attr('height', resize_height);
            var ctx = canvas[0].getContext('2d');
            ctx.clearRect(0,0,0,0);
            ctx.drawImage(image,
                0, 0, image.width, image.height,
                0, 0, resize_width, resize_height
                );
            var source_base64 = canvas.get(0).toDataURL(imageType);
            source_img = source_base64.split(',')[1]
        }
        image.src = e.target.result;
    }
    source_reader.readAsDataURL(file);

    let img = document.createElement('img');
    img.id = 'upload_img';
    img.width = $('#drop_area').outerWidth();
    img.height = $('#drop_area').outerHeight();
    let disp_reader = new FileReader();
    disp_reader.onload = function () {
        img.src = disp_reader.result;
        $('#preview_field').append(img);
    }
    disp_reader.readAsDataURL(file);
}



// アイコン画像を消去するボタン
$('#img_delete_button').on('click', function () {
    if (!communicate_status) {
        source_img = null;
        $('#preview_field').empty();
        $('#input_file').val('');
        $('#drop_area').show();
        $('#img_delete_button').hide();
        $('#drop_area').css('border', '5px dashed #aaa');
    }
});

// target
$(function () {
    // クリックで画像を選択する場合
    $('#target_drop_area').on('click', function () {
        if (!communicate_status) {
            $('#target_input_file').click();
        }
    });
    $('#target_input_file').on('change', function () {
        // 画像が複数選択されていた場合
        if (this.files.length > 1) {
            notify_alert('ファイルが多すぎます', 'アップロードできる画像は1つだけです。', false);
            $('#target_input_file').val('');
            return;
        }
        target_handleFiles(this.files);
    });
});
    
// ドラッグしている要素がドロップ領域に入ったとき・領域にある間
$('#target_drop_area').on('dragenter dragover', function (event) {
    if (!communicate_status) {
        event.stopPropagation();
        event.preventDefault();
        $('#target_drop_area').css('border', '5px solid #333');  // 枠を実線にする
    }
});

// ドラッグしている要素がドロップ領域から外れたとき
$('#target_drop_area').on('dragleave', function (event) {
    if (!communicate_status) {
        event.stopPropagation();
        event.preventDefault();
        $('#target_drop_area').css('border', '5px dashed #ccc');  // 枠を点線に戻す
    }
});

// ドラッグしている要素がドロップされたとき
$('#target_drop_area').on('drop', function (event) {
    if (!communicate_status) {
        event.preventDefault();
        $('#target_input_file')[0].files = event.originalEvent.dataTransfer.files;
        // 画像が複数選択されていた場合
        if ($('#target_input_file')[0].files.length > 1) {
            notify_alert('ファイルが多すぎます', 'アップロードできる画像は1つだけです。', false);
            $('#target_input_file').val('');
            $('#target_drop_area').css('border', '5px dashed #ccc');  // 枠を点線に戻す
            return;
        }
        target_handleFiles($('#target_input_file')[0].files);
    }
});

// 選択された画像ファイルの操作
var target_img = null;
var target_file = null;
function target_handleFiles(files) {
    target_file = files[0];
    var imageType = 'image.*';
    // ファイルが画像が確認する
    if (!target_file.type.match(imageType)) {
        notify_alert('非対応のファイルです', '画像を入れてください。', false);
        $('#target_input_file').val('');
        $('#target_drop_area').css('border', '5px dashed #ccc');
        return;
    }
    $('#target_drop_area').hide();
    $('#target_img_delete_button').show();
    
    const resize_width = 512;
    const resize_height = 512;
    let image = new Image();
    let target_reader = new FileReader();
    target_reader.onload = function(e) {
        image.onload = function() {
            var canvas = $('#canvas_tar').attr('width', resize_width).attr('height', resize_height);
            var ctx = canvas[0].getContext('2d');
            ctx.clearRect(0,0,0,0);
            ctx.drawImage(image,
                0, 0, image.width, image.height,
                0, 0, resize_width, resize_height
                );
            var target_base64 = canvas.get(0).toDataURL(imageType);
            target_img = target_base64.split(',')[1]
        }
        image.src = e.target.result;
    }
    target_reader.readAsDataURL(target_file);

    let img = document.createElement('img');
    img.id = 'target_upload_img';
    img.width = $('#target_drop_area').outerWidth();
    img.height = $('#target_drop_area').outerHeight();
    let reader = new FileReader();
    reader.onload = function () {
        img.src = reader.result;
        $('#target_preview_field').append(img);
    }
    reader.readAsDataURL(target_file);
}



$(window).resize(function () {
    $('#upload_img').width($('#drop_area').outerWidth());
    $('#upload_img').height($('#drop_area').outerHeight());
    $('#target_upload_img').width($('#target_drop_area').outerWidth());
    $('#target_upload_img').height($('#target_drop_area').outerHeight());
});

// アイコン画像を消去するボタン
$('#target_img_delete_button').on('click', function () {
    if (!communicate_status) {
        target_img = null;
        $('#target_preview_field').empty();  // 表示していた画像を消去
        $('#target_input_file').val('');  // inputの中身を消去
        $('#target_drop_area').show();  // drop_areaをいちばん前面に表示
        $('#target_img_delete_button').hide();  // clear_buttonを非表示
        $('#target_drop_area').css('border', '5px dashed #aaa');  // 枠を点線に変更
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

// 入力する文に関しての関数です
var text_length = 0;
$('#textarea').on('input', function() {
    let remove_space_text = ($('#textarea').val()).replace(/\s+/g, '');
    text_length = remove_space_text.length;
    check();
});

function text_check(text) {
    let modify_text = '';
    if (!text){
        modify_text = '';
    }
    else {
        modify_text = text;
    }
    return modify_text;
};

// 画像サイズに関するボタンです
$('#size_256').addClass('add_Color');
var img_size = '256';
$('.set_size_button').click(function () {
    if (!communicate_status) {
        let img_size_button_id = this.id;
        $('.set_size_button').removeClass('add_Color');
        $('#' + img_size_button_id).addClass('add_Color');
        let img_size_split = img_size_button_id.split('_');
        img_size = img_size_split[1];
    }
});

// 選択の確認
function check() {
    let text_length_status = (text_length > 0 ? true : false);
    let start_status = text_length_status;
    if (start_status && communication_status) {
        $('#start_button').removeClass('disabled');
    }
    else {
        $('#start_button').addClass('disabled');
    }
};
// サーバーIPアドレスとの通信が可能かを確認
var communication_status = false;
$('#communication_partner').focusout(function(){
    send_data = {
        version: ICON_VARSION
    };
    let check_version_data = JSON.stringify(send_data);
    $.ajax({
        url: "http://" + $('#communication_partner').val() + ":5050/test",
        method: "POST",
        data: check_version_data,
        dataType: "json",
        timeout: 10000,
        async: true, // 同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
        .done(function (r_data) {
            communication_status = true;
            check();
            if (r_data['pre_diagnostics'] !== 0){
                let pre_check_list = test_device_status(r_data['pre_diagnostics']);
                let notice_sting = "Something went wrong.\n" + pre_check_list[0];
                notify_alert("Oops!", notice_sting, false, pre_check_list[1]);
            }
        })
        .fail(function () {
            communication_status = false;
            check();
            notify_alert("サーバーにアクセス出来ません", "Server IP Addressを確認してください。", false);
            let button = $('#footer_position_row').offset().top;
            $('body,html').animate({ scrollTop:  button}, 600, 'swing');
        });
})

// 開始後に関する関数です
function stop_input() {
    let advanced_param_list = Object.keys(MODEL_PARAM[model_button_id][param_button_id])
    for (let i = 0; i < advanced_param_list.length; i++) {
        $('#' + advanced_param_list[i] + '_slider').prop('disabled', true);
    };
    $('#start_button').fadeOut(0);
    $('#reload').fadeOut(0);
    $('#textarea').prop('disabled', true);
    $('.seed_radio_button').prop('disabled', true);
    $('#carrot_textarea').prop('disabled', true);
    $('#stick_textarea').prop('disabled', true);
    $('#communication_partner').prop('disabled', true);
}

// 中止ボタンを押された際に送信データを変更する
var abort = false;
function abort_signal() {
    if (!img_path_check){
        $('#result_img').attr("src", "../static/demo_img/icon/whiteout.png");
    }
    $('#quit_button').fadeOut(0);
    $('#progress_bar').fadeOut(300);
    abort = true;
};



// 待機の場合に表示する関数
function wait_display() {
    const top_list = [10, 14, 19, 27, 38];
    const fontsize_list = [70, 85, 110, 150, 200];
    const color_list = ['rgba(0, 0, 0, 1)', 'rgba(20, 20, 20, 1)', 'rgba(40, 40, 40, 1)', 'rgba(60, 60, 60, 1)', 'rgba(70, 70, 70, 1)'];
    $('#loader_wrap').fadeIn(0);
    for (i = 1; i < 6; i++) {
        let css_lib = {
            'font-size': fontsize_list[i-1],
            'top': top_list[i-1] + '%',
            'position': 'fixed',
            'display': 'flex',
            'width': '100vw',
            'height': '100vh',
            'align-items': 'center',
            'justify-content': 'center',
            'color': color_list[i-1]
        }
        $('#waiting_num_display').append('<i class="material-icons" id="waiter_' + i + '">person</i>')
        $('#waiter_' + i).css(css_lib);
    };
};

// 待機の状態に自分の位置を知らせる関数
function sort_order(priority, model_status) {
    const color_list_ = ['rgba(82, 119, 148, 1)', 'rgba(62, 95, 124, 1)', 'rgba(47, 77, 107, 1)', 'rgba(30, 58, 89, 1)', 'rgba(10, 35, 65, 1)'];
    priority = priority > 5 ? 5 : priority;
    for (let i = 1; i < 6; i++) {
        $('#waiter_' + i).css('color', color_list_[i-1]);
    }
    $('#waiter_' + priority).css('color', 'rgba(248, 87, 8, 1)');

    if ((priority === 1) && model_status) {
        $('#loader_wrap').fadeOut(0);
    }
};

// 生成開始ボタンに関しての関数
var communicate_status = false;
var hash = '00000000-0000-0000-0000-000000000000';
function start() {
    stop_input();
    $('#footer').fadeOut(0);
    $.cookie('url', $('#communication_partner').val())
    communicate_status = true;
    wait_display();
    $('#img_make_container').fadeIn(0);
    $('#save_buttons').fadeOut(0);
    const target = $('#img_make_container').get(0).offsetTop;
    $('body,html').animate({ scrollTop: target }, 600, 'swing');
    
    // スライダーの値を取得
    const slider_vals = get_slider_values();
    const seed_value = get_seed_value();


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
        seed: parseInt(seed_value),
        size: parseInt(img_size),
        source_img: source_img,
        target_img: target_img,
        hash: hash,
        abort: false,
        carrot: text_check($('#carrot_textarea').val()),
        stick: text_check($('#stick_textarea').val())
    };
    let send_json_data = JSON.stringify(send_data);
    communicate(send_json_data);
};

// 通信に関しての関数
var jqxhr;
var img_path_check = false;
function communicate(s_data) {
    if (JSON.parse(s_data)["abort"]) {
        jqxhr.abort();
    }
    jqxhr = $.ajax({
        url: "http://" + $('#communication_partner').val() + ":5050/service",
        method: "POST",
        data: s_data,
        dataType: "json", // データの受信形式
        timeout: 10000,
        async: false, // 同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
        .done(function (r_data, textStatus, xhr) {
            sort_order(r_data["priority"], r_data["model_status"]);
            img_path_check = r_data["img_path"];
            tmp_data = JSON.parse(s_data);
            // サーバーサイド側の問題の有無を確認
            if (r_data["diagnostics"] !== 0) {
                $('#result_img').attr("src", "../static/demo_img/icon/whiteout.png");
                let error_string = make_error_string(r_data["diagnostics"]);
                error_string = 'サーバーサイドで以下のエラーが発生しました。\n' + error_string;
                notify_alert("Backend Error", error_string);
            }

            // プログレスバーの表示
            if (r_data['current_iter'] === null) {
                r_data['current_iter'] = 0;
            }
            $('.determinate').attr('style', 'width:' + (100 * r_data['current_iter']/tmp_data['total_iter']) + '%');

            // 生成画像の表示
            if (!(r_data["img_path"] === null)) {
                let img_path = r_data["img_path"].replace('..', 'http://' + $('#communication_partner').val() + ':5050');
                $('#result_img').attr("src", img_path).on("load", function () {
                    $('#result_img').fadeIn();
                });
            }
            // 通信継続の確認
            if (!r_data["complete"]) {
                if (abort){
                    tmp_data["abort"] = true;
                }
                tmp_data["source_img"] = null;
                tmp_data["target_img"] = null;
                wait(300).done(function () {
                    tmp_data["hash"] = r_data["hash"];
                    hash = r_data["hash"];
                    communicate(JSON.stringify(tmp_data));
                });
            } else {
                $('#quit_button').fadeOut(0);
                $('#progress_bar').fadeOut(300, function(){
                    $('#save_buttons').fadeIn(0);
                });
                if (r_data) {
                    let download_img_path = r_data["img_path"].replace('..', 'http://' + $('#communication_partner').val() + ':5050');
                    let download_mp4_path = r_data["mp4_path"].replace('..', 'http://' + $('#communication_partner').val() + ':5050');
                    $('#download_img').attr("href", download_img_path).attr("download", $("#textarea").val() + ".png");
                    $('#download_mp4').attr("href", download_mp4_path).attr("download", $("#textarea").val() + '.mp4');
                }
                else {
                    $('#download_img').attr("href", download_img_path).attr("download", $("#textarea").val() + ".png");
                    $('#download_mp4').attr("href", download_mp4_path).attr("download", $("#textarea").val() + '.mp4');
                }
                if ($('#Notification_box').prop("checked") === true) {
                    PushNotification(r_data["img_path"])
                }
            }
        })
        .fail(function (r_data, textStatus, error) {
            notify_alert("通信失敗", "Server IP Addressを確認してください。");
        });
}

function notify_alert(alert_title, alert_text, reload=true , show_icon="error") {
    swal({
        title: alert_title,
        text: alert_text,
        icon: show_icon,
    });
    $('.swal-button').click(function() {
        if (reload){
            window.location.reload();
        }
    });
}

function test_device_status(device_status) {
    let alert_text = "";
    let check_list = [];
    let icon = 'warning';
    let binary_device_status = device_status.toString(2);
    binary_device_status = parseInt(binary_device_status, 2);
    if (binary_device_status & 0B0001) {
        alert_text = alert_text + '・Minor version conflict (Ver. ' + ICON_VARSION + ')\n　レイアウト等が乱れる可能性があります。\n';
    }
    if ((binary_device_status >>> 1) & 0B0001) {
        alert_text = alert_text + '・Major version conflict (Ver. ' + ICON_VARSION + ')\n　管理者にお問い合わせください。\n';
        icon = 'error';
    }
    if ((binary_device_status >>> 2) & 0B0001) {
        alert_text = alert_text + '・GPU not found\n　管理者にお問い合わせください。\n';
        icon = 'error';
    }
    if ((binary_device_status >>> 3) & 0B0001) {
        alert_text = alert_text + '・TensorCore not found\n　画像生成速度が低下する可能性があります。';
    }
    check_list.push(alert_text, icon);
    return check_list;
}

function make_error_string(error_value) {
    let error_cause = "";
    let binary_error_value = error_value.toString(2);
    binary_error_value = parseInt(binary_error_value, 2);

    if (binary_error_value & 0B0001) {
        error_cause = error_cause + '・Translation error\n　管理者にお問い合わせください。\n';
    }
    if ((binary_error_value >>> 1) & 0B0001) {
        error_cause = error_cause + '・Out of memory error\n　(Tips：「仕上がりの選択」をmiddleにしてください。)\n';
    }
    if ((binary_error_value >>> 2) & 0B0001) {
        error_cause = error_cause + '・Unexpected error\n　管理者にお問い合わせください。';
    }
    return error_cause;
}

function wait(msec) {
    var objDef = new $.Deferred();
    setTimeout(function () {
        objDef.resolve(msec);
    }, msec);
    return objDef.promise();
}

// Twitterへの変更じ関する関数です
$('.twitter').click(function () {
    let twitter_button = this.id;
    let path = "";
    let mode = "";
    if (twitter_button === "tweet") {
        path = $('#download_img').attr("href");
        mode = "tweet";
    }
    else if (twitter_button === "change_icon") {
        path = $('#download_img').attr("href");
        mode = "icon"
    }
    // 送信するデータ
    twitter_data = {
        img_path: path,
        mode: mode,
        text: $('#textarea').val()
    };
    let twitter_send_data = JSON.stringify(twitter_data);

    $.ajax({
        url: "http://" + $('#communication_partner').val() + ":5050/twitter/auth",
        method: "POST", // HTTPメソッドの種別
        data: twitter_send_data,
        dataType: "json", // データの受信形式
        timeout: 10000, // タイムアウト値（ミリ秒）
        async: false, // 同期通信  false:同期  true:非同期
        contentType: "application/json; charset=utf-8",
    })
        .done(function (r_data, textStatus, xhr) {
            if (r_data['is_set_env_var']) {
                window.open(r_data["authorization_url"]);
            }else {
                notify_alert('Oops!','現在、Twitter関連の機能がご利用頂けません。\n管理者にお問い合わせください。', false);
            }
        })
        .fail(function (r_data, textStatus, xhr) {
            notify_alert('Oops!','現在、Twitter関連の機能がご利用頂けません。\n管理者にお問い合わせください。', false);
        });
});

// 通知に関しての関数
function PushNotification(img_path) {
    Push.create('AIconです。', {
        body: '画像を作り終えました！',
        icon: img_path,
        timeout: 5000,
        onClick: function () {
            this.close();
        }
    });
}

// バージョン表示に関する部分です
$('#copyright_position').text('AIcon ' + ICON_VARSION + '　Copyright © 2021 MagicSpell')
