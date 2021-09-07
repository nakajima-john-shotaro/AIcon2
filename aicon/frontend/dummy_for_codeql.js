$(document).ready(function(){
    $('ul.tabs').tabs({
        swipeable : true,
        responsiveThreshold : 1920
    });
});

$(document).ready(function(){
    $('.sidenav').sidenav();
});

$(document).ready(function(){
    $('.carousel').carousel();
});

$(document).ready(function(){
$('select').formSelect();
});

$(function () {
    $('.cancelEnter')
        .on('keydown', function (e) {
            if (e.key == 'Enter') {
                return false;
            }
        })
});

function ClearTextArea() {
    $("#ja_text").val("");
}

function reload() {
    window.location.reload();
}

function get_range_value() {
    const slider = document.getElementById("slider")
    return slider.value;
}

function start() {
    // 使用するmodel
    const use_model = document.getElementById("use_model").value;

    // スライダーの値を取得
    const slider_val = get_range_value()
    
    // 表示するやつ（※後で削除する）
    document.getElementById("info").textContent = use_model;
    const val = document.getElementById("output")
    val.innerText = slider_val
}