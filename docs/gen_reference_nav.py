"""
Generate the code reference pages and navigation.

Taken inspiration from:
    * https://github.com/mkdocstrings/mkdocstrings/blob/master/docs/gen_ref_nav.py
    * https://github.com/liquidinvestigations/hoover-snoop2/blob/master/docs/gen.py
"""
from pathlib import Path

import mkdocs_gen_files

CODE_ROOT = 'opal'

nav = mkdocs_gen_files.Nav()  # type: ignore[no-untyped-call]

for path in sorted(Path(CODE_ROOT).glob('**/*.py')):
    doc_path = Path('reference', path.relative_to('.')).with_suffix('.md')
    # fully qualified name
    ident = '.'.join(path.relative_to('.').with_suffix('').parts)

    # skip database migrations
    if '.migrations' in ident:
        continue

    # add mapping from Python file name to generated Markdown page
    # the path needs to be relative to the SUMMARY.md file
    # i.e., without "reference/" prefix if the index is in the same directory
    parts = tuple(path.parts)
    nav[parts] = str(path.relative_to('.').with_suffix('.md'))

    # write Markdown file for module
    with mkdocs_gen_files.open(doc_path, 'w') as fd:
        print(f'::: {ident}', file=fd)

    mkdocs_gen_files.set_edit_path(doc_path, Path('..', path))

# generate index page with list of code reference pages
# will be picked up by literate-nav to show the navigation for the code reference
with mkdocs_gen_files.open('reference/SUMMARY.md', 'w') as nav_file:
    nav_file.writelines(nav.build_literate_nav())
