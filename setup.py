from setuptools import setup
from setuptools import find_packages

version = "0.1.0"

install_requires = [
    "acme>=1.7.0",
    "certbot>=1.7.0",
    "setuptools",
    "mock",
    "oci"
]

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.rst")) as f:
    long_description = f.read()

setup(
    name="certbot_oci_certs",
    version=version,
    description="OCI Certs Management Service plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/therealcmj/certbot-oci-certs",
    author="Chris Johnson",
    author_email="christopher.johnson@oracle.com",
    license="Apache License 2.0",
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        # I only tested this with Python 3.10
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "certbot.plugins": [
            "oci = certbot_oci_certs.installer:OCIInstaller"
        ]
    },
    test_suite="certbot_oci_certs"
)
