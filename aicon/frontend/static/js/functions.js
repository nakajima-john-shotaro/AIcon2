// $('#BigSleep_example').hide()
// $('#DALL-E_example').hide()
// materializeが原因で脳筋手法に出ます
// 今後はもっと汎用性のあるものを作ります…
var DeepDaze_button_active = false;
var BigSleep_button_active = false;
$("#DeepDaze").click(function(){
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
});

$("#BigSleep").click(function(){
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
});


var model_list = ['DeepDaze', 'BiGSleep', 'DALL-E'];


$('.Model_Area').click( function() {
    let img_id_list = [];
    $(".carousel-item").each(function() {
        img_id_list.push('#'+$(this).attr('id'));
    });
    console.log(img_id_list)

    if (DeepDaze_button_active) {
        console.log("DeepDaze")
        // $('.gallery').fadeOut("slow", function() {
            for (let i = 0; i < img_id_list.length; i++){
                $(img_id_list[i]).attr('src',"https://lorempixel.com/250/250/nature/"+ (i+1))
            };
            $(document).ready(function(){
                $('.carousel').carousel();
            });
        // });
    }
    else if (BigSleep_button_active) {
        console.log("BigSleep")
        for (let i = 0; i < img_id_list.length; i++){
            let tmp = img_id_list[i];
            $(tmp).attr('src',"https://lorempixel.com/250/250/cats/"+(i+1))
            console.log(img_id_list[i])
            console.log($(img_id_list[i]).attr('src'))
        };
        $(document).ready(function(){
            $('.carousel').carousel();
        });
    }
        let src = $(img_id_list[1]).attr('src');
        console.log(src);

    // if (DeepDaze_button_active) {
    //     console.log("DeepDaze")
    //     $('.gallery').fadeOut("slow", function() {
    //         $('#DeepDaze_example').fadeIn('slow');
    //     });
    // }
    // else if (BigSleep_button_active) {
    //     console.log("BigSleep")
    //     $('.gallery').fadeOut("slow", function(){
    //         $('#BigSleep_example').fadeIn('slow');
    //     });
    // }
});

$(window).on('load resize', function() {
    var windowWidth = window.innerWidth;
    var elements = $('#fixed-area');
    if (windowWidth >= 768) {
    Stickyfill.add(elements);
    }else{
    Stickyfill.remove(elements);
    }
});


// 後から直す
// $(document).ready(function() {
//     $("#use_model").change(function() {
//         const model = $(this).val();
//         if (model === 'DeepDaze'){
//             $('.carousel').fadeOut('slow');
//             $('#DeepDaze_example').fadeIn('slow');
//         }else if (model === 'BigSleep') {
//             $('.carousel').fadeOut(100);
//             $('#BigSleep_example').fadeIn(200);
//         }else if (model === 'DALL-E') {
//             $('.carousel').fadeOut('slow');
//             $('#DALL-E_example').fadeIn('slow');
//         }
//     })
// });

$(function () {
    $('.cancelEnter')
        .on('keydown', function (e) {
            if (e.key == 'Enter') {
                return false;
            }
        })
});

$(window).load(function(){
	$('html,body').animate({ scrollTop: 0 }, '1');
});
$('#reload').on('click',function(){
    location.reload();
	$('html,body').animate({ scrollTop: 0 }, '1');
});


function get_range_value() {
    const slider = document.getElementById("slider")
    return slider.value;
}

function select_check() {
    let use_model = "";
    if (DeepDaze_button_active === true) {
        use_model = "DeepDaze";
    }
    else if (BigSleep_button_active === true) {
        use_model = "BigSleep";
    }
    else {
        use_model = "";
        console.log("使用するモデルを選択してください");
    }
    return use_model;
}

function start() {
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
    console.log(input_text);
    console.log("↑入力された文字列");

    // 送信するデータ
    send_data = {
        model_name : use_model,
        text : input_text,
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
