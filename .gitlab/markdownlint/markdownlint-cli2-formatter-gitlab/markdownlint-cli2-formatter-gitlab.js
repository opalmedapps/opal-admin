/**
 * Inspired by:
 *    * markdownlint-cli2-formatters, e.g., https://github.com/DavidAnson/markdownlint-cli2/blob/main/formatter-junit/markdownlint-cli2-formatter-junit.js
 *    * eslint-formatter-gitlab: https://gitlab.com/remcohaszing/eslint-formatter-gitlab/-/blob/main/index.js
 */
// @ts-check
"use strict";

/**
 * @typedef {object} CodeClimateLines
 * @property {number} begin
 * @property {number} [end]
 */

/**
 * @typedef {object} CodeClimateContents
 * @property {string} body
 */

/**
 * @typedef {object} CodeClimateLocation
 * https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#locations
 * @property {string} path
 * @property {CodeClimateLines} lines
 */

/**
 * @typedef {object} CodeClimateIssue
 * https://github.com/codeclimate/platform/blob/master/spec/analyzers/SPEC.md#issues
 * @property {'issue'} type
 * @property {string} check_name
 * @property {string} description
 * @property {CodeClimateContents} [contents]
 * @property {'info' | 'minor' | 'major' | 'critical' | 'blocker'} severity
 * @property {string} fingerprint
 * @property {CodeClimateLocation} location
 */

const fs = require('node:fs').promises;
const path = require('node:path');

const { createHash } = require('node:crypto');

/**
 * @param {string} filePath The path to the linted file.
 * @param {string} ruleName The name of the rule
 * @param {string} description The description of the violation
 * @returns {string} The fingerprint for the violation
 */
 function createFingerprint(filePath, ruleName, description) {
  const md5 = createHash('md5');
  md5.update(filePath);
  md5.update(ruleName);
  md5.update(description);

  return md5.digest('hex');
}

// Writes markdownlint-cli2 results to a file in JSON format following the GitLab CodeClimate spec
// see: https://docs.gitlab.com/ee/ci/testing/code_quality.html#implementing-a-custom-tool
const outputFormatter = (options, params) => {
  const { directory, results } = options;
  const { name, spaces } = (params || {});

  let issues = [];

  for (const errorInfo of results) {
    const { fileName, lineNumber, ruleNames, ruleDescription, errorDetail, errorContext, errorRange } = errorInfo;

    const ruleName = ruleNames.join("/");
    const errorDetailText = errorDetail ? ` [${errorDetail}]` : "";
    const text = `${ruleName}: ${ruleDescription}${errorDetailText}`;
    const lineNumberEnd = (errorRange) ? errorRange[1] : lineNumber;

    /** @type {CodeClimateIssue} */
    const issue = {
      type: 'issue',
      check_name: ruleName,
      description: text,
      severity: 'minor',
      fingerprint: createFingerprint(fileName, ruleName, ruleDescription),
      location: {
        path: fileName,
        lines: {
          begin: lineNumber,
        },
      },
    };

    issues.push(issue);
  }

  const content = JSON.stringify(issues, null, spaces || 2);
  return fs.writeFile(
    path.resolve(
      // eslint-disable-next-line no-inline-comments
      directory /* c8 ignore next */ || "",
      name || "markdownlint-cli2-results.json"
    ),
    content,
    "utf8"
  );
};

module.exports = outputFormatter;
