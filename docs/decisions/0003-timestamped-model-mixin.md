---
# SPDX-FileCopyrightText: Copyright (C) 2026 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
number: 3
status: proposed
date: 2026-02-23
---

# Timestamped model mixin

## Context and Problem Statement

We have various places where we add `DateTimeField`s to a model to track when it was created and/or modified.
It would be good to have a mixin that provides the ability for a timestamped model.

## Decision Drivers

- Implementation effort
- Test effort
- Maintenance effort

## Considered Options

- [`TimeStampedModel`](https://django-model-utils.readthedocs.io/en/latest/models.html#timestampedmodel) mixin provided by [`django-model-utils`](https://django-model-utils.readthedocs.io/en/latest/index.html)
- `TimeStampedModel` provided by [`django-extensions`](https://django-extensions.readthedocs.io/en/latest/model_extensions.html#database-model-extensions)
- Our own model living in the `core` app

## Decision Outcome

Chosen option: We will use the timestamped model from `django-model-utils` because it is well tested and has type hints.

### Consequences

- Need to keep another package up to date.

#### Unrelated consequence

`django-extensions` should already be a dev dependency, move it to dev dependency.

## Pros and Cons of the Options

### Model from `django-model-utils`

Dedicated package for models.

- Last release in September 2024
- Well-tested model: https://github.com/jazzband/django-model-utils/blob/master/tests/test_models/test_timestamped_model.py
- Has other models and managers that could be helpful in the future
- Package has type hints

### Model from `django-extensions`

We already use this package.

- No additional dependency necessary
- Need to make it available in all environments making certain management commands available in production
- Package does not have type hints causing `Call to untyped function "CreationDateTimeField" in typed context` and `Call to untyped function "ModificationDateTimeField" in typed context`
- Last release in April 2025
- Has some tests:
    - https://github.com/django-extensions/django-extensions/blob/main/tests/test_timestamped_model.py
    - https://github.com/django-extensions/django-extensions/blob/main/tests/test_modificationdatetime_fields.py
    - creation field does not seem to have tests

### Our own model

- Additional implementation effort
- Also need to write tests
- Not reliant on third-party dependency
