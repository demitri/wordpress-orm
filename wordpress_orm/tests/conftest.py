
# This test configuration file is automatically called by pytest.

# Run this on the command line to see what fixtures are available:
#
# % py.test --fixtures
#

# To prevent STDOUT from being captured, add "--capture=no"

import pytest
from ..api import API
from requests.auth import HTTPBasicAuth

#
# Fixtures are pytest resources used for testing. Define fixtures here.
# At the very least, the application must be defined as a fixure named "app".
# A "client" fixture is defined by the pytest-flask extension.
#
# A test function can access a fixture when you provide the fixture name in
# the test function argument list, e.g. `def test_thing(app)`.
#
# Fixture scopes can be one of: "function" (default), "class", "module", "session".
# Ref: https://docs.pytest.org/en/latest/fixture.html#scope-sharing-a-fixture-instance-across-tests-in-a-class-module-or-session
#
# function - one fixture is created for each test function
# class    - one fixture is created for each Python test class (if tests are defined that way)
# module   - one fixture is created for each module (i.e. test_*py file)
# session  - one fixture is reused over the entire test session over all tests

@pytest.fixture(scope="session") #, params=["dev", "production"])
def wp_api(request):
	'''
	Instance of the WordPress API object.
	'''
	# Read parameters from "request.param". If more than one
	# parameter is provided, more than one fixture is created
	# and the tests repeated with it.
	# There is no need to iterate over the parameters in this code.
	# Ref: https://docs.pytest.org/en/2.8.7/fixture.html#parametrizing-a-fixture
	
	# if request.param == "wp_server_dev":
	#	return wordpress_orm.API(url= <WP dev URL>)
	# elif request.param == "wp.server_prod":
	#	return wordpress_orm.API(url= <WP prod URL>)

	wordpress = API()
	
	wordpress.base_url = "http://brie6.cshl.edu/wordpress/index.php/wp-json/wp/v2/"
	wordpress.authenticator = HTTPBasicAuth('', '')
	
	return wordpress








