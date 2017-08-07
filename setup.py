import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, 'README.rst')).read()
changes = open(os.path.join(here, 'CHANGES.rst')).read()


requires = [
    'pyramid>=1.7',
    'requests',
    'future',
]

tests_require = [
    'mock',
    'responses',
    'zope.testing',
]

setup(
    name='pyramid_heroku',
    version='0.1.3',
    description='A bunch of helpers for successfully running Pyramid on Heroku.',
    long_description=readme + '\n' + changes,
    classifiers=[
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    packages=['pyramid_heroku'],
    install_requires=requires,
    author='NiteoWeb Ltd.',
    author_email='info@niteoweb.com',
    license='BSD',
    url='https://github.com/niteoweb/pyramid_heroku',
    keywords='pyramid heroku pylons web',
    tests_require=requires + tests_require,
    test_suite='pyramid_heroku',
)
