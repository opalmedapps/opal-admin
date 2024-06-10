const fs = require('fs')
const path = require('path')

// Define required dependency files
const dependencies = new Map()

// Bootstrap
dependencies.set('bootstrap/dist/css/bootstrap.min.css', 'bootstrap/css/bootstrap.min.css')
dependencies.set('bootstrap/dist/css/bootstrap.min.css.map', 'bootstrap/css/bootstrap.min.css.map')
dependencies.set('bootstrap/dist/js/bootstrap.bundle.min.js', 'bootstrap/js/bootstrap.bundle.min.js')
dependencies.set('bootstrap/dist/js/bootstrap.bundle.min.js.map', 'bootstrap/js/bootstrap.bundle.min.js.map')
// Fontawesome
dependencies.set('@fortawesome/fontawesome-free/css/fontawesome.min.css', 'fontawesomefree/css/fontawesome.min.css')
dependencies.set('@fortawesome/fontawesome-free/css/solid.min.css', 'fontawesomefree/css/solid.min.css')
dependencies.set('@fortawesome/fontawesome-free/css/regular.min.css', 'fontawesomefree/css/regular.min.css')
// the CSS files reference the webfonts
dependencies.set('@fortawesome/fontawesome-free/webfonts/fa-solid-900.ttf', 'fontawesomefree/webfonts/fa-solid-900.ttf')
dependencies.set('@fortawesome/fontawesome-free/webfonts/fa-solid-900.woff2', 'fontawesomefree/webfonts/fa-solid-900.woff2')
dependencies.set('@fortawesome/fontawesome-free/webfonts/fa-regular-400.ttf', 'fontawesomefree/webfonts/fa-regular-400.ttf')
dependencies.set('@fortawesome/fontawesome-free/webfonts/fa-regular-400.woff2', 'fontawesomefree/webfonts/fa-regular-400.woff2')
// Unpoly
dependencies.set('unpoly/unpoly.min.css', 'unpoly/css/unpoly.min.css')
dependencies.set('unpoly/unpoly-bootstrap5.min.css', 'unpoly/css/unpoly-bootstrap5.min.css')
dependencies.set('unpoly/unpoly.min.js', 'unpoly/js/unpoly.min.js')
dependencies.set('unpoly/unpoly-bootstrap5.min.js', 'unpoly/js/unpoly-bootstrap5.min.js')

const modules_directory = path.join(process.cwd(), 'node_modules')
const target_directory = process.cwd()

dependencies.forEach((targetFile, sourceFile) => {
    source = path.join(modules_directory, sourceFile)
    target = path.join(target_directory, targetFile)

    console.log(`copying ${source} to ${target}`)

    fs.copyFile(source, target, (err) => {
        if (err) {
            console.error('Error copying file:', err)
            process.exit(1)
        }
    })
})
