from setuptools import find_packages, setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

setup(
    name='river_reacher',
    package_dir={"": "src"},
    packages=find_packages('src'),
    version='0.0.0',
    description='River reach spatial data management.',
    long_description=long_description,
    author='Joel McCune (https://github.com/knu2xs)',
    license='Apache 2.0',
)
