const patientCBox = document.getElementById('checkallP');
const questionCBox = document.getElementById('checkallQ');

patientCBox.addEventListener('change', e => {
    if(e.target.checked === true) {
        var ele=document.getElementsByName('patIds');
        for(var i=0; i<ele.length; i++){
            ele[i].selected=true;
        }
    }else{
        var ele=document.getElementsByName('patIds');
        for(var i=0; i<ele.length; i++){
            ele[i].selected=false;
        }
    }
});

questionCBox.addEventListener('change', e => {
    if(e.target.checked === true) {
        var ele=document.getElementsByName('questionIDs');
        for(var i=0; i<ele.length; i++){
            if(ele[i].type=='checkbox'){
                ele[i].checked=true;
            }
        }
    }else{
        var ele=document.getElementsByName('questionIDs');
        for(var i=0; i<ele.length; i++){
            if(ele[i].type=='checkbox'){
                ele[i].checked=false;
            }
        }
    }
});

function updateEndDate() {
    var start_date = document.getElementById("start").value;
    document.getElementById("end").value = document.getElementById("end").max;
    document.getElementById("end").setAttribute("min",start_date);
}
