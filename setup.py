import os
from setuptools import setup, find_packages
import userpypi

def fread(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

try:
    reqs = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).read()
except (IOError, OSError):
    reqs = ''

setup(
    name='userpypi',
    version=userpypi.get_version(),
    description="A Django application that emulates the Python Package Index.",
    long_description=fread("README.rst")+"\n\n"+fread('Changelog.rst')+"\n\n"+fread('AUTHORS.rst'),
    classifiers=[
        "Framework :: Django",
        "Development Status :: 4 - Beta",
        #"Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Software Distribution",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='django pypi packaging index',
    author='Ask Solem',
    author_email='askh@opera.com',
    maintainer='Benjamin Liles',
    maintainer_email='benliles@gmail.com',
    url='http://github.com/benliles/chishop',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
)
