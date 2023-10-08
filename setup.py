from pathlib import Path

from setuptools import setup

from onboardapis import __version__

__project_name__ = "onboardapis"
__description__ = "A pure Python wrapper for the on-board APIs of many different transportation providers"
__author__ = "Felix Zenk"
__email__ = "felix.zenk@web.de"
__license__ = "MIT"
__url__ = "https://github.com/felix-zenk/onboardapis"

readme = Path("README.md").read_text()

setup(
    name=__project_name__,
    version=__version__,
    packages=[__project_name__],
    url=f"https://felix-zenk.github.io/projects/{__project_name__}",
    license=__license__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    long_description=readme,
    long_description_content_type="text/markdown",
    project_urls={
        "Bug Tracker": f"{__url__}/issues",
        "Source": __url__,
        "Documentation": f"https://{__project_name__}.readthedocs.io/en/latest",
    },
    python_requires=">=3.6",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
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
