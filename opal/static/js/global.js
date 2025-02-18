// SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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
