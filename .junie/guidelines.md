# Project Guidelines

This project is a Django fullstack project, using a synchronous queue (django-queuebie) to implement CQRS.

All Django apps are located in the "apps" directory, including the configuration (containing settings) as "config" app.

## Unit tests

* Unit tests are written in pytest
* Mocking is the last resort. If it's required, we'll use it but other ways are preferred
* It's OK to create model instances in unittests if it's required, we use FactoryBoy for that
* Tests are to be located in the exact file structure as the to-be-tested file, just within the "test" directory and
  prefixed with "test_*.py" (apps/account/models/user.py -> apps/account/tests/models/test_user.py)
* We always aim for branch-coverage, meaning every way through an if-statement is supposed to have it's own test
* Unit-tests are supposed to be atomic and test only one thing
