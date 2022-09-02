from setuptools import setup, find_packages

from onboardapis import __project_name__, __description__, __version__, __author__, __email__, __license__, __url__

with open('README.md', mode='r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name=__project_name__,
    version=__version__,
    packages=find_packages(".", exclude=["tests", "tests.*", "examples", "examples.*"]),
    url=f"https://felix-zenk.github.io/projects/{__project_name__}",
    license=__license__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    long_description=readme,
    long_description_content_type='text/markdown',
    project_urls={
        'Bug Tracker': f"{__url__}/issues",
        'Source': __url__,
        'Documentation': f"https://{__project_name__}.readthedocs.io/en/latest",
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Utilities'
    ],
)

