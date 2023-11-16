#!/usr/bin/env python
"""The setup script for bbatch."""

from setuptools import setup

with open("README.md") as readme_file:
    readme = readme_file.read()


setup(
    author="Nick Alberelli",
    author_email="nick@blender.org",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Command line tool to perform recursive crawl blend files from the console",
    long_description=readme,
    include_package_data=True,
    keywords="bbatch",
    name="bbatch",
    packages=[
        "bbatch",
        "bbatch.default_scripts",
    ],
    version="0.1.1",
    entry_points={"console_scripts": ["bbatch = bbatch.__main__:main"]},
    package_data={'bbatch.default_scripts': ['*']},
)
