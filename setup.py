from setuptools import setup, find_packages

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

version = '0.9.2'

LONG_DESCRIPTION = """
=======================
Kev
=======================

K.E.V. (Keys, Extra Stuff, and Values) is a Python ORM for key-value \
stores and document databases based on Valley. Currently supported \
backends are Redis, S3 and a S3/Redis hybrid backend.

"""

setup(
    name='kev',
    version=version,
    description="""K.E.V. (Keys, Extra Stuff, and Values) is a Python \
    ORM for key-value stores and document databases based on Valley. \
    Currently supported backends are Redis, S3, and a \
    S3/Redis hybrid backend.""",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='redis, s3',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    url='https://github.com/capless/kev',
    license='GPLv3',
    install_requires=parse_requirements('requirements.txt'),
    include_package_data=True,
    zip_safe=False,
)
