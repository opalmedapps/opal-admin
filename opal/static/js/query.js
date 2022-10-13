$("#checkallQ").click(function (){
    if ($("#checkallQ").is(':checked')){
        $(".checkboxesQ").each(function (){
            $(this).prop("checked", true);
        });
    }else{
        $(".checkboxesQ").each(function (){
            $(this).prop("checked", false);
        });
    }
});

$("#checkallP").click(function (e){
    e.preventDefault()
    if ($("#checkallP").is(':checked')){
        $(".optionP").each(function (){
            $(this).prop("selected", true);
        });
    }else{
        $(".optionP").each(function (){
            $(this).prop("selected", false);
        });
    }
});
