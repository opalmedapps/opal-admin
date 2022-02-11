from pathlib import Path

import mkdocs_gen_files

CODE_ROOT = 'opal'

with mkdocs_gen_files.open('module-index.md', 'w') as index:
    print('# Module index\n', file=index)

    for path in Path(CODE_ROOT).glob('**/*.py'):
        doc_path = Path('reference', path.relative_to('.')).with_suffix('.md')
        ident = '.'.join(path.relative_to('.').with_suffix('').parts)

        # skip database migraitons
        if '.migrations' in ident:
            continue

        # write file
        with mkdocs_gen_files.open(doc_path, 'w') as fd:
            print('::: ' + ident, file=fd)

        # write entry in module index file
        print(f'- [`{ident}`][{ident}]', file=index)

        mkdocs_gen_files.set_edit_path(doc_path, Path('..', path))
