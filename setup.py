from setuptools import setup, find_packages
import sys, os

version = '0.01'

setup(
    name='ckanext-dariahshibboleth',
    version=version,
    description="Shibboleth authentication for DARIAH",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Carsten Thiel',
    author_email='thiel@sub.uni-goettingen.de',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.dariahshibboleth'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        dariahshibboleth=ckanext.dariahshibboleth.plugin:DariahShibbolethPlugin
    ''',
)
