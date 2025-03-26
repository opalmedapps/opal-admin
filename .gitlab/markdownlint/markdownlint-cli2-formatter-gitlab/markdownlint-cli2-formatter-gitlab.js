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
 * @param {string} violation The complete textual description of the violation
 * @returns {string} The SHA256 fingerprint for the violation
 */
const createFingerprint = function createFingerprint (violation) {
  const sha256 = createHash("sha256");
  sha256.update(violation);
  return sha256.digest("hex");
};


// Writes markdownlint-cli2 results to a file in JSON format following the GitLab CodeClimate spec
// see: https://docs.gitlab.com/ee/ci/testing/code_quality.html#implementing-a-custom-tool
const outputFormatter = (options, params) => {
  const { directory, results } = options;

  let issues = [];

  for (const errorInfo of results) {
    const { fileName, lineNumber, ruleNames, ruleDescription, errorDetail, errorContext, errorRange } = errorInfo;

    const ruleName = ruleNames.join("/");
    const errorDetailText = errorDetail ? ` [${errorDetail}]` : "";
    const text = `${ruleName}: ${ruleDescription}${errorDetailText}`;
    const column = (errorRange && errorRange[0]) || 0;
    const columnText = column ? `:${column}` : "";
    const description = ruleDescription +
          (errorDetail ? ` [${errorDetail}]` : "") +
          (errorContext ? ` [Context: "${errorContext}"]` : "");
    // construct error text with all details to use for unique fingerprint
    // avoids duplicate fingerprints for the same violation on multiple lines
    const errorText =
      `${fileName}:${lineNumber}${columnText} ${ruleName} ${description}`;

    /** @type {CodeClimateIssue} */
    const issue = {
      type: 'issue',
      check_name: ruleName,
      description: text,
      severity: 'minor',
      fingerprint: createFingerprint(errorText),
      location: {
        path: fileName,
        lines: {
          begin: lineNumber,
        },
      },
    };

    issues.push(issue);
  }

  const content = JSON.stringify(issues);
  return fs.writeFile(
    path.resolve(
      directory,
      "markdownlint-cli2-results.json"
    ),
    content,
    "utf8"
  );
};

module.exports = outputFormatter;
