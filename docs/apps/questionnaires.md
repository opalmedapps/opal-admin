# Questionnaires

The `questionnaires` app provides functionalities for interacting with questionnaire data.

## Exporting Reports

Currently, the only functionality provided in this app is to expose a launching point for the external ePRO Questionnaires reporting tool originally developed by Luc Galarneau.

Due to the sensitivity of this data, the `Export Reports` page is only viewable by administrative users and any additional users who have been granted the custom permission `export_report` from the admin portal. This custom permission is defined in the `ExportReportPermission` model. Technically, it is an implementation of a 'model-less permission' as described in reference links 2 & 3.

### References

1. [Original Reporting Tool Repo]( https://gitlab.com/opalmedapps/opalquestionnairesDB )
2. [How can I use Django permissions without defining a content type or model?]( https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model )
3. [Django Permissions without a Model]( https://github.com/surfer190/fixes/blob/master/docs/django/django-permissions-without-a-model.md )
