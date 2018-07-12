
from ..entities.user import User, UserRequest

def test_user_query(wp_api):
	'''
	Basic test to see that users can be queried.
	'''
	uq = wp_api.UserRequest()
	users = uq.get()

	assert uq.response.status_code == 200, "Could not connect to: '{0}'".format(wp_api.base_url)
	assert len(users) > 0, "No users found in the WordPress installation."
	assert isinstance(users[0], User), "The object returned from the UserRequest was not a User class as expected."

