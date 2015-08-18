from setuptools import setup, find_packages
from distutils.core import Extension

setup(name='wntr',
    version='0.1',
    description='Water iNfrastucture Tool for Resilience',
    url='https://software.sandia.gov/git/resilience',
    license='Revised BSD',
    packages=find_packages(),
    zip_safe=False)

