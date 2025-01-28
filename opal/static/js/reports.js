// SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

function openXlsx(){
    let xlsx_options_div = document.getElementById("xlsx_options_div");
    xlsx_options_div.style.display = "";
}

function cancel(){
    let xlsx_options_div = document.getElementById("xlsx_options_div");
    xlsx_options_div.style.display = "none";
}
