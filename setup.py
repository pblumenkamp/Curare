
from os import path
from setuptools import setup, find_packages
import curare.metadata


# Get the long description from the README file
setup_dir = path.abspath(path.dirname(__file__))
with open(path.join(setup_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='Curare',
    version=curare.metadata.__version__,
    description='Curare: A Customizable and Reproducible Analysis Pipeline for RNA-Seq Experiments',
    keywords=['bioinformatics', 'rna-seq', 'differential-gene-expression', 'transcriptomics'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='GPLv3',
    author='Patrick Blumenkamp',
    author_email='patrick.blumenkamp@computational.bio.uni-giessen.de',
    url='https://github.com/pblumenkamp/Curare',
    packages=find_packages(include=['curare', 'curare.*']),
    python_requires='>=3.9',
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        'PyYAML == 5.4.1',
        'docopt == 0.6.2',
        'snakemake == 6.3'
    ],
    entry_points={
        'console_scripts': [
            'curare=curare.curare:main',
            'curare_wizard=curare.curare_wizard:main'
        ]
    },
    classifiers=[
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Natural Language :: English'
    ],
    project_urls={
        'Bug Reports': 'https://https://github.com/pblumenkamp/Curare/issues',
        'Source': 'https://github.com/pblumenkamp/Curare'
    },
)