import os
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers
import ckan.model
import requests

import uuid
import logging
import pprint

log = logging.getLogger("ckanext.dariahshibboleth")

class DariahShibbolethPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthenticator)

    def update_config(self, config):
        # use our login form
        toolkit.add_template_directory(config, 'templates')

    def get_auth_functions(self):
        return {}

    def login(self):
        #try getting user data from Shibboleth
        userdict = get_shib_data(self)
        if userdict:
            #check if the user exists
            user = get_user(userdict['eppn'])
            if not user:
                # create ckan user
                log.error('no  user with eppn: ' + userdict['eppn'])
                user = toolkit.get_action('user_create')(
                    context={'ignore_auth': True},
                    data_dict={'email': userdict['mail'],
                        'openid': userdict['eppn'],
                        'name': userdict['name'],
                        'fullname': userdict['cn'],
                        'password': str(uuid.uuid4())})
            else:
                log.error('exists eppn: '+ userdict['eppn'])
            self.identify()

    def identify(self):
        #try getting user data from Shibboleth
        userdict = get_shib_data(self)
        if userdict:
            toolkit.c.user = userdict['name']

    def logout(self):
        pass
    def abort(self, status_code, detail, headers, comment):
        pass


def get_shib_data(self):
    # take the data from the environment, default to blank
    mail = toolkit.request.environ.get('mail','')
    eppn = toolkit.request.environ.get('eppn','')
    cn = toolkit.request.environ.get('cn','')
    # return something only if there is a mail address
    if mail == '':
        return None
    else:
        userdict={'mail': mail,
            'eppn': eppn,
            'name': generate_user_name(cn),
            'cn': cn}
        return userdict


def get_user(eppn):
    user = ckan.model.User.by_openid(eppn)
    return user

def generate_user_name(string):
    # actual username generation - TODO: GLOBALLY UNIQUE
    return string.replace(" ", "").lower()


