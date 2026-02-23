---
# SPDX-FileCopyrightText: Copyright (C) 2026 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later
number: 1
status: proposed
date: 2026-02-23
---

# Use Markdown Architectural Decision Records

_This ADR was inspired by https://adr.github.io/madr/decisions/0000-use-markdown-architectural-decision-records.html._

## Context and Problem Statement

We want to record architectural decisions made in this project independent whether decisions concern the architecture ("architectural decision record"), the code, or other fields.
Which format and structure should these records follow?

## Considered Options

- [Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — The first incarnation of the term "ADR"
- [MADR](https://adr.github.io/madr/) 4.0.0 — The Markdown Architectural Decision Records
- Formless – No conventions for file format and structure

## Decision Outcome

Chosen option: "MADR 4.0.0", because

- Recommended by `adrs` to use for new projects
- Metadata can be captured via YAML frontmatter
- The MADR project is maintained
- MADR has more sections which aligns more with what we need

## Consequences

Need a still maintained ADR tool to facilitate easy creation and maintenance of decisions.

For a lightweight ADR toolset, see [`adrs`](https://joshrotenberg.com/adrs/index.html) or the original [`adr-tools`](https://github.com/npryce/adr-tools).
