# coding=utf-8

from setuptools import find_packages, setup

with open("README.rst") as f:
    readme = f.read()

setup(
    name="cee_syslog_handler",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(exclude=["tests"]),
    author="Blue Yonder GmbH",
    author_email="peter.hoffmann@blue-yonder.com",
    url="https://github.com/blue-yonder/cee_syslog_handler",
    description="Python Syslog Logging Handler with CEE Support",
    long_description=readme,
    license="new BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
