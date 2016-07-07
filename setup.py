from setuptools import setup,find_packages
 
version = '0.2'
 
LONG_DESCRIPTION = """
=======================
Redes
=======================

A declarative syntax Python ORM for Redis+ElasticSearch based on the official Redis and ElasticSearch Python libraries.

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
    keywords='cloudant, couchdb, django',
    author='Brian Jinwright',
    author_email='opensource@ipoots.com',
    maintainer='Brian Jinwright',
    packages=find_packages(),
    
    license='Apache',
    install_requires=['redis','elasticsearch','boto3'],
    include_package_data=True,
    zip_safe=False,
)
