# Questionnaires

The `questionnaires` app provides functionalities for interacting with questionnaire data.

## Export Reports

The ePRO Questionnaires Reporting tool was originally developed by Luc Galarneau as a standalone utility: [ePRO Questionnaires reporting tool][questionnaire-reporting-repo].

Due to the sensitivity of this data, the `Export Reports` page is only viewable by administrative users and any additional users who have been granted the custom permission `export_report` from the admin portal. This custom permission is defined in the `ExportReportPermission` model. Technically, it is an implementation of a 'model-less permission' as described in [How can I use Django permissions without defining a content type or model?][django-modelless-perms-stackoverflow] & [Django Permissions without a Model][django-modelless-perms-github]

### Adding an authorized user

**Note that any researcher requesting ePRO data must have already received Research Ethics Board approval.**

First create a basic OpalAdmin account for the authorized researcher if they do not already have one:

1. Login as superuser to the admin portal.
2. Select `Users` > *Add User +*
3. Provide a Username and secure password according to the instructions and hit *SAVE*.

To grant the `export_report` permission:

1. Return to the `Users` menu
2. Search for the username of the user you just created and click the username.
3. Scroll down to the `User Permissions` section, and filter to "questionnaires"
4. Hit the right arrow with the permission selected to grant this user the export reports permission.
5. Scroll down and hit *SAVE*.
6. Alternatively, you could add this user to an existing group which already contains the export reports permission.

### Launching the reporting tool & exporting reports

1. Login to OpalAdmin as a user with `export_report` permissions.
2. Navigate to `Export Reports`.
3. A new user will have no Questionnaire Profile information. Proceed to the `View all questionnaires` page.
4. Select the desired questionnaire from the drop down menu. Only questionnaires present in QuestionnaireDB connected to this instance of the Backend are viewable.
5. Hit `Select`. In the filter page, toggle the `Follow in my dashboard` checkbox if you want fast access to this questionnaire in the future.
6. Adjust the date, questions, and patients filters to your specifications.
7. Click `View Report`
8. View results and optionally export as CSV or Excel
9. Return to the first `Export Reports` page and verify your questionnaire profile now displays the saved questionnaire.

<!-- Link identifiers -->
[django-modelless-perms-github]: https://github.com/surfer190/fixes/blob/master/docs/django/django-permissions-without-a-model.md
[django-modelless-perms-stackoverflow]: https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model
[questionnaire-reporting-repo]: https://gitlab.com/opalmedapps/opalquestionnairesDB
