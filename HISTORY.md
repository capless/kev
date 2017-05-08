# History

### 0.9.1

- Removed Python 2 support
- Added backup and restore feature
- Upgraded to valley 1.3.0

### 0.9.0

- Fixed S3 backend filters
- Added logic to make it easy to switch _create_error_dict
- Added check_unique method on Document so it easier to do these validations in Formy

### 0.8.1

- Fixed get_index_name for backends other than DynamoDB
- Added more context to docs on DynamoDB index names

### 0.8.0

- Added DynamoDB backend
- Added SlugField and EmailField
- Integrated with Valley
 
### 0.7.0

- Added S3 only backend
- Added wildcard filtering for Redis and S3/Redis backends (credit: JamieCressey)
- Updated README docs
- Added HISTORY.md

### 0.6.3

- changed the id scheme, completed most methods for s3 only backend
- fixed setup.py

### 0.5.2
- Added backend_id to doc_id and index id (fixes #5), fixed boolean indexing and saving as an int problem (fixes #6), removed a bunch of document instantiations (fixes #7), also fixed tests

### 0.5.1

- Fixed date and datetime validators and properties

### 0.5
- Removed list for ```all``` queries and added generators
- Fixed ValueErrors
- Updated Readme

### 0.4
- Refactored for Python 3
- Added travis-ci config

### 0.3

- updated ```__repr__``` and documentation in README

### 0.2

- Added more defined roles for the db and indexer attributes

### 0.1

- Merged code from Redes project (Redis-only backend) with a hybrid S3/Redis backend
