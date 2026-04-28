# noqa: INP001
# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
    module_path = path.relative_to('.').with_suffix('')
    doc_path = Path('reference', path.relative_to('.')).with_suffix('.md')

    parts = tuple(module_path.parts)

    if parts[-1] == '__init__':
        parts = parts[:-1]
        doc_path = doc_path.with_name('index.md')

    # fully qualified name
    ident = '.'.join(parts)

    # skip database migrations
    if 'migrations' in parts:
        continue

    # add mapping from Python file name to generated Markdown page
    # the path needs to be relative to the SUMMARY.md file
    # i.e., without "reference/" prefix if the index is in the same directory
    nav[parts] = doc_path.relative_to('reference').as_posix()

    # write Markdown file for module
    with mkdocs_gen_files.open(doc_path, 'w') as fd:
        fd.write(f'::: {ident}\n')

    mkdocs_gen_files.set_edit_path(doc_path, Path('..', path))

# generate index page with list of code reference pages
# will be picked up by literate-nav to show the navigation for the code reference
with mkdocs_gen_files.open('reference/SUMMARY.md', 'w') as nav_file:
    nav_file.writelines(nav.build_literate_nav())
