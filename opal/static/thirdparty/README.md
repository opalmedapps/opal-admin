<!--
SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Opal Backend Third-Party JS Dependencies

The `package.json` located within this directory tracks the JS dependencies.
These dependencies are used for the UI of the Django-based backend.

A `postinstall` script (`copy_distribution_files`) exists to copy the required distribution files to the corresponding directory that is then used in the template to include the static files.

## Future Goal

It remains to be investigated whether it is possible to automatically update these dependencies using _Renovate Bot_.

Potential hook:

- https://docs.renovatebot.com/configuration-options/#postupgradetasks
- https://docs.renovatebot.com/configuration-options/#updatelockfiles
