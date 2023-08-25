/*
    Initialize bootstrap tooltips
    See: https://getbootstrap.com/docs/5.3/components/tooltips/#enable-tooltips
*/

up.compiler('[data-bs-toggle="tooltip"]', (element) => {
    new bootstrap.Tooltip(element)
})
