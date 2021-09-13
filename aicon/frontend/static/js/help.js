$('#wrapper').multiscroll({
    sectionsColor: ['#333', '#444', '#555','#333', '#444', '#555'],//セクションごとの背景色設定
    anchors: ['select_model', 'slider', 'input_text','source_image','option'],//セクションとリンクするページ内アンカーになる名前
    menu: '#menu',//上部ナビゲーションのメニュー設定
    navigation: true,//右のナビゲーション出現、非表示は false
    navigationTooltips:['Select Model', 'Slider', 'Input Text','Source Image','Option'],//右のナビゲーション現在地時に入るテキスト
    loopTop: true,//最初のセクションを上にスクロールして最後のセクションまでスクロールするかどうかを定義します。
    loopBottom: true,//最後のセクションを下にスクロールして最初のセクションまでスクロールするかどうかを定義します。
});