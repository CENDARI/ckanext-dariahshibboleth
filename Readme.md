DARIAH Shibboleth authentication plugin for CKAN
===================

Implemented for and tested with CKAN 2.2.
Development has been discontinued in favor of a CENDARI specific implementation: https://github.com/CENDARI/ckanext-cendari

Features
-------------------
- login via Shibboleth
- create CKAN account from Shibboleth data if it does not yet exist
- update username and email address on login if necessary

Missing
-------------------
- support for federations, currently the username is reduced to the ePPN's local part
- assign roles/groups based on Shibboleth data
- disable local login


