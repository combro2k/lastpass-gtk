import setuptools

from distutils.core import setup

setup(
    name='lastpassgtk',
    version='0.1dev',
    packages=['lastpassgtk',],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.txt').read(),
    entry_points = {
        'console_scripts': ['lastpass-gtk=lastpassgtk.lastpassgtk:main'],
    },
    install_requires=[
        'gtk3',
        'zenipy',
    ],
)
