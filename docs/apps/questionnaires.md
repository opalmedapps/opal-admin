# Questionnaires




The `questionnaires` app provides functionalities for interacting with questionnaire data.

## Export Reports




Currently, the only functionality provided in this app is to expose a launching point for the external [ePRO Questionnaires reporting tool][questionnaire-reporting-repo] originally developed by Luc Galarneau.

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

*[2022-09-28] Note that currently, the reporting tool must be running in a separate django instance and connected to a production QuestionnaireDB (due to filtering out of test patient responses which are not pertinent to research).*
*Additionally, there must already be an account created for the researcher in the reporting tool app itself, either using django's `createsuperuser` functionality, or through it's own admin portal.*

1. Login to OpalAdmin as a user with `export_report` permissions.
2. Select `Export Reports` > `ePRO Data Extractions` this will automatically launch a new window connecting to the reporting tool.
3. Login to the reporting tool with the dedicated researcher/user account existing in the reporting tool's database.
4. Click `View all questionnaires` to display the list of available ePRO questionnaires for which there exists production data.
5. Select desired questionnaire, optionally tick "Follow in my dashboard" for easier future access
6. Filter results by any combination of data range, patient ids, and questions.
7. Click `View Report`
8. View results and optionally export as CSV or Excel



<!-- Link identifiers -->
[django-modelless-perms-github]: https://github.com/surfer190/fixes/blob/master/docs/django/django-permissions-without-a-model.md
[django-modelless-perms-stackoverflow]: https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model
[questionnaire-reporting-repo]: https://gitlab.com/opalmedapps/opalquestionnairesDB
