import re
from distutils.core import setup

from setuptools import find_packages


def get_property(prop, project):
    with open(project + '/__init__.py', 'r') as f:
        result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), f.read())
    return result.group(1)

project_name = 'pyImageStack'

setup(
    name=project_name,
    version=get_property('__version__', project_name),
    packages=find_packages(),
    url='https://github.com/NiklasKroeger/pyImageStack',
    license='',
    author='Niklas Kröger',
    author_email='niklas@kroeger.dev',
    description='A thin wrapper around PyTables to create very large stacks of images'
)
