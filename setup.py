#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("requirements.txt", "r") as reqs:
    requirements = reqs.readlines()

setup(
    name="builder",
    version="1.0.0-rc1",
    description="manage container builds in a single repo",
    author="Philip Bove",
    install_requires=requirements,
    author_email="phil@bove.online",
    packages=find_packages(),
    scripts=["bin/builder.py"],
)
