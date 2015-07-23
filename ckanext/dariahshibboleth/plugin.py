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
    """ 
    Main plugin class implemeting ``IConfigurer`` and ``IAuthenticator``.
    """

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthenticator)

    def update_config(self, config):
        """
        Add our extended login form template with Shibboleth link to CKAN's toolkit.
        """
        toolkit.add_template_directory(config, 'templates')

    def get_auth_functions(self):
        """ Pass. """
        return {}

    def login(self):
        """
        Performs the actual login, if Shibboleth data is found by :py:func:`get_shib_data`.

        If the a CKAN user with the ePPN does not exist, he is created.
        Otherwise full name and mail address are updated if neccessary.

        Finally, a pylons session is created for session management.
        """
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
        """
        Extracts the logged in user from the pylons session.
        """
        # try getting user from pylons session
        pylons_user_name = pylons.session.get('ckanext-dariahshibboleth-user')
        if pylons_user_name:
            toolkit.c.user = pylons_user_name

    def logout(self):
        """
        Log out the user by destroying the pylons session and redirecting to Shibboleth logout.
        """
        # destroy pylons session (ckan)
        if 'ckanext-dariahshibboleth-user' in pylons.session:
            del pylons.session['ckanext-dariahshibboleth-user']
            pylons.session.save()
        # redirect to shibboleth logout
        toolkit.redirect_to(controller='util',action='redirect',url='/Shibboleth.sso/Logout')

    def abort(self, status_code, detail, headers, comment):
        """ Simply passes through an abort. """
        return status_code, detail, headers, comment


def get_shib_data(self):
    '''
    Extracts full name, email address and ePPN from Shibboleth data.

    :returns: user_dict containing the data or ``None`` if no Shibboleth data is found.
    '''
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
    """
    Look up CKAN user by ePPN.

    :param eppn: String holding the ePPN to look up.
    :returns: user_dict of the user or ``None``.
    """
    user = ckan.model.User.by_openid(eppn)
    if not user:
        return None
    else:
        user_dict = toolkit.get_action('user_show')(data_dict={'id': user.id})
        return user_dict

def generate_user_name(eppn):
    """
    Returns a valid username by defaulting to the ePPN's local part.
    This is not federation-ready!

    :param eppn: The ePPN to extract the username from.
    :returns: Lower cased local part of ePPN.
    """
    # actual username generation
    return eppn.split('@')[0].lower()

def hash_email(email):
    """
    Create a CKAN style hash from an email.

    :param email: The email address to hash.
    :returns: hex encoded md5 hash of the normalized email.
    """
    e = email.strip().lower().encode('utf8')
    return md5(e).hexdigest()

