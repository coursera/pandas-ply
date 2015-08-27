from distutils.core import setup
setup(
    name = 'pandas-ply',
    version = '0.2.1',
    author = 'Coursera Inc.',
    author_email = 'pandas-ply@coursera.org',
    packages = [
        'pandas_ply',
        'pandas_ply.vendor',
    ],
    description = 'functional data manipulation for pandas',
    long_description = open('README.rst').read(),
    license = 'Apache License 2.0',
    url = 'https://github.com/coursera/pandas-ply',
    classifiers = [],
)
