
class WordPressORMException(Exception):
	''' Base exception for this module. '''
	pass

class NoEntityFound(WordPressORMException):
	''' No WordPress entity was found. '''
	pass

class MultipleEntitiesFound(WordPressORMException):
	''' Multiple entities were returned when one was expected. '''
	pass

class BadRequest(WordPressORMException):
	''' Bad HTTP request (400). '''
	pass
	
class AuthenticationRequired(WordPressORMException):
	''' Authentication required for this request. '''
	pass

class UserNotFound(WordPressORMException):
	''' WordPress user not found. '''
	pass

class MissingRequiredParameter(WordPressORMException):
	''' A required parameter was missing. '''
	pass

