from pathlib import Path
from setuptools import setup

from onboardapis import __version__

setup(
    name='onboardapis',
    version=__version__,
    packages=['onboardapis'],
    url="https://felix-zenk.github.io/projects/onboardapis",
    license="MIT",
    author="Felix Zenk",
    author_email="felix.zenk@web.de",
    description="A pure Python wrapper for the on-board APIs of many different transportation providers",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    project_urls={
        "Bug Tracker": "https://github.com/felix-zenk/onboardapis/issues",
        "Source": 'https://github.com/felix-zenk/onboardapis',
        "Documentation": "https://onboardapis.readthedocs.io/en/latest",
    },
    python_requires=">=3.7",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
