$(document).ready(function () {
    var table = $('#sitesTable').DataTable({
        "responsive": true,
        "lengthChange": false,
        "autoWidth": false,
        // "columnDefs": [
        //     { "orderable": false, "targets": [4] }
        // ],
        "buttons": [
            {
                "text": '<i class="fas fa-plus"></i> New site',
                "id": "add-button",
                "className": "btn btn-primary",
                "action": function (e, dt, node, config) {
                    location.href = window.location.origin + '/hospital-settings/site/create/';
                }
            }
        ]
    }).buttons().container().appendTo('#sitesTable_wrapper .col-md-6:eq(0)');
});
