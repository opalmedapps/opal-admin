/*
    Initialize bootstrap tooltips
    See: https://getbootstrap.com/docs/5.3/components/tooltips/#enable-tooltips
*/

up.compiler('[data-bs-toggle="tooltip"]', (element) => {
    let tooltip = new bootstrap.Tooltip(element)

    // dispose the tooltip when the anchor element is removed
    // see: https://github.com/unpoly/unpoly/discussions/576
    up.destructor(element, () => {
        tooltip.dispose()
    })
})
