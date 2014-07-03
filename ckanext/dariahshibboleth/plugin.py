import os
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers
import ckan.model
import requests
import pylons

import uuid
import logging
import pprint
from hashlib import md5

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
        # try getting user data from Shibboleth
        userdict = get_shib_data(self)
        if userdict:
            # check if the user exists
            user = get_user(userdict['eppn'])
            if not user:
                # create ckan user
                user = toolkit.get_action('user_create')(
                    context={'ignore_auth': True},
                    data_dict={'email': userdict['mail'],
                        'openid': userdict['eppn'],
                        'name': userdict['name'],
                        'fullname': userdict['cn'],
                        'password': str(uuid.uuid4())})
                log.info('newly created and logged in user with eppn: ' + userdict['eppn'])
            else:
                # check whether we need to update something
                if not ((user['fullname']==userdict['cn']) or (user['email_hash']==userdict['mail'])):
                    # update ckan user based on shibboleth data (plus password reset)
                    user = toolkit.get_action('user_update')(
                        context={'ignore_auth': True},
                        data_dict={'id': user['id'],
                            'email': userdict['mail'],
                            'fullname': userdict['cn'],
                            'password': str(uuid.uuid4())})
                    log.info('updated user with eppn: '+ userdict['eppn'])
                for key, value in user.iteritems():
                    log.error(key)
                log.info('logged in existing user with eppn: '+ userdict['eppn'])
            # save user to pylons session
            pylons.session['ckanext-dariahshibboleth-user'] = user['name']
            pylons.session.save()
            # redirect to dashboard
            toolkit.redirect_to(controller='user', action='dashboard')

    def identify(self):
        # try getting user from pylons session
        pylons_user_name = pylons.session.get('ckanext-dariahshibboleth-user')
        if pylons_user_name:
            toolkit.c.user = pylons_user_name

    def logout(self):
        # destroy pylons session (ckan)
        if 'ckanext-dariahshibboleth-user' in pylons.session:
            del pylons.session['ckanext-dariahshibboleth-user']
            pylons.session.save()
        # redirect to shibboleth logout
        toolkit.redirect_to(controller='util',action='redirect',url='/Shibboleth.sso/Logout')

    def abort(self, status_code, detail, headers, comment):
        return status_code, detail, headers, comment


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
            'name': generate_user_name(eppn),
            'cn': cn}
        return userdict


def get_user(eppn):
    user = ckan.model.User.by_openid(eppn)
    if not user:
        return None
    else:
        user_dict = toolkit.get_action('user_show')(data_dict={'id': user.id})
        return user_dict

def generate_user_name(string):
    # actual username generation - TODO: GLOBALLY UNIQUE
    return string.split('@')[0].lower()

def hash_email(email):
    e = email.strip().lower().encode('utf8')
    return md5(e).hexdigest()

