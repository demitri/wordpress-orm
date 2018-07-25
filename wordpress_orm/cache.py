
class WPORMCacheObjectNotFoundError(Exception):
	pass

class WPORMCache:
	def __init__(self):
		self.initialize()

	def initialize(self):
		'''
		Internal method to set up the cache from scratch.
		'''
		self.cache = dict()	

	def get(self, class_name=None, key=None):
		'''
		Method to retrieve wordpress-orm entity from cache; key can be WordPress 'id' or slug.
		Keys that are not strings are coerced to type 'str' (i.e. an id of 4 or "4" is equivalent).
		
		class_name : class name as string
		'''
		if key is not None and isinstance(key, str) is False:
			key = str(key)
		if class_name not in self.cache:
			self.cache[class_name] = dict()
		try:
			return self.cache[class_name][key] #.get(key, None) # return 'None' if key is not found
		except KeyError:
			raise WPORMCacheObjectNotFoundError("Object of class '{0}' with key='{1}' not found".format(class_name, key))
	
	def set(self, value=None, keys=list()):
		'''
		Method to set values in the cache. Typically keys is a tuple or list containing the WordPress id and slug.
		Keys that are not strings are coerced to type 'str' (i.e. an id of 4 or "4" is equivalent).
		'''
#		if key is not None and isinstance(key, str) is False:
#			key = str(key)
		class_name = type(value).__name__
		if class_name not in self.cache:
			self.cache[class_name] = dict()
		for key in [k for k in keys if k is not None]: # safeguard against any key value that might be None
			if isinstance(key, str) is False:
				key = str(key)
			self.cache[class_name][key] = value

	def clear(self):
		'''
		Clear all items from the cache.
		'''
		self.initialize()
