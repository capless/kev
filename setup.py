from setuptools import setup,find_packages
 
version = '0.2'
 
LONG_DESCRIPTION = """
=======================
Kev
=======================

K.E.V. (Keys, ElasticSearch, and Values) is a Python ORM for key-value stores and ElasticSearch. Currently supported backends are Redis and a S3/Redis hybrid backend.
"""
 
setup(
    name='redes',
    version=version,
    description="""This project should make it easier for devs to use Redis+ElasticSearch with Python.""",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment",
    ],
    keywords='redis, elasticsearch, s3, key-value',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    
    license='Apache',
    install_requires=['redis==2.10.5','elasticsearch==2.3.0','boto3==1.3.1'],
    include_package_data=True,
    zip_safe=False,
)
