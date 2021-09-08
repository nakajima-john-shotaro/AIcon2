$(function () {
    $('.cancelEnter')
        .on('keydown', function (e) {
            if (e.key == 'Enter') {
                return false;
            }
        })
});

function reload_window() {
    window.location.reload();
}

function get_range_value() {
    const slider = document.getElementById("slider")
    return slider.value;
}

function start() {
    // 使用するmodel
    const use_model = document.getElementById("use_model").value;
    console.log(use_model)
    // スライダーの値を取得
    const slider_val = get_range_value()
    
    // 表示するやつ（※後で削除する）
    // document.getElementById("info").textContent = use_model;
    // const val = document.getElementById("output")
    // val.innerText = slider_val

    // 送信するデータ
    send_data = {
        model_name : use_model,
        text : "Hi! I'm John. Nice to meet you!",
        total_iter : parseInt(slider_val),
        size : 256,
        hash : '00000000-0000-0000-0000-000000000000',
        abort : false,
    };
    const send_json_data = JSON.stringify(send_data)
    communicate(send_json_data)
}

function wait(msec) {
    var objDef = new $.Deferred();
    setTimeout(function () {
        objDef.resolve(msec);
    }, msec);
    return objDef.promise();
}

function communicate(s_data) {
    $.ajax({
        url: "http://slack.tasakilab:8081/",
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
