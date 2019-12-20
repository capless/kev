from setuptools import setup, find_packages

try: # Fix for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt', session=False)

version = '0.9.2'

LONG_DESCRIPTION = """
=======================
Kev
=======================

K.E.V. (Keys, Extra Stuff, and Values) is a Python ORM for key-value \
stores and document databases based on Valley. Currently supported \
backends are Redis, S3, DynamoDB and a S3/Redis hybrid backend.

"""

setup(
    name='kev',
    version=version,
    description="""K.E.V. (Keys, Extra Stuff, and Values) is a Python \
    ORM for key-value stores and document databases based on Valley. \
    Currently supported backends are Redis, S3, DynamoDB and a \
    S3/Redis hybrid backend.""",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='redis, s3, dynamodb',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    url='https://github.com/capless/kev',
    license='Apache',
    install_requires=[str(ir.req) for ir in install_reqs],
    include_package_data=True,
    zip_safe=False,
)
