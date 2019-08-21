import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, "README.rst")).read()
changes = open(os.path.join(here, "CHANGES.rst")).read()


setup(
    name="pyramid_heroku",
    version="0.6.0",
    description="A bunch of helpers for successfully running Pyramid on Heroku.",
    long_description=readme + "\n" + changes,
    classifiers=[
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Framework :: Pylons",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=["pyramid_heroku"],
    install_requires=["expandvars", "pyramid>=1.7", "requests"],
    author="Niteo",
    author_email="info@niteo.co",
    license="BSD",
    url="https://github.com/niteoweb/pyramid_heroku",
    keywords="pyramid heroku pylons web",
    test_suite="pyramid_heroku",
)
