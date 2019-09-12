import os
from setuptools import setup, find_packages

# We allow commented lines in this file
project_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(project_dir, 'requirements/base.in')) as f:
    install_requires = [line.rstrip('\n') for line in f if not line.startswith('#')]

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "version.txt")) as f:
    version = f.read().rstrip()

setup(
    name="balrogscript",
    version=version,
    description="TaskCluster Balrog Script",
    author="Mozilla Release Engineering",
    author_email="release+python@mozilla.com",
    url="https://github.com/mozilla-releng/balrogscript",
    packages=find_packages(),
    package_data={
        "balrogscript": ["data/*"],
        "": ["version.json"],
    },
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "balrogscript = balrogscript.script:main",
        ],
    },
    license="MPL2",
    install_requires=install_requires,
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ),
)
