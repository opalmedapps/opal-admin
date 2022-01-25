$(document).ready(function () {
    var table = $('#institutionsTable').DataTable({
        "responsive": true,
        "lengthChange": false,
        "autoWidth": false,
        "columnDefs": [
            { "orderable": false, "targets": [3] }
        ],
        "buttons": [
            {
                "text": '<i class="fas fa-plus"></i> New institution',
                "id": "add-button",
                "className": "btn btn-primary",
                "action": function (e, dt, node, config) {
                    location.href = window.location.origin + '/hospital-settings/institution/create/';
                }
            }
        ]
    }).buttons().container().appendTo('#institutionsTable_wrapper .col-md-6:eq(0)');
});
