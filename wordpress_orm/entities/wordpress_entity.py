
from abc import ABCMeta, abstractmethod, abstractproperty

import requests

context_values = ["view", "embed", "edit"]

class WPSchema():
	'''
	Object representing the schema for each WordPress entity.
	'''
	#
	# Properties are defined based on the field names, see below.
	#
	pass	

class WPEntity(metaclass=ABCMeta):
	'''
	Abstract superclass for all entities of the WordPress API.
	'''
	def __init__(self, api=None):
		
		if api is None:
			raise Exception("Use the 'API.{0}()' method to create a new '{0}' object.".format(self.__class__.__name__))
		
		self.api = api			   # holds the connection information
		self.json = None		   # holds the raw JSON returned from the API
		self.s = WPSchema()		   # an empty object to use to hold custom properties
		self._schema_fields = None # a list of the fields in the schema
		
		# define the schema properties for the WPSchema object
		for field in self.schema_fields:
			setattr(self.s, field, None)
		
	@abstractproperty
	def schema_fields(self):
		'''
		This method returns a list of schema properties for this entity, e.g. ["id", "date", "slug", ...]
		'''
		pass

	def add_schema_field(self, new_field):
		'''
		Method to allow extending schema fields.
		'''
		assert isinstance(new_field, str)
		new_field = new_field.lower()
		if new_field not in self._schema_fields:
			self._schema_fields.append(new_field)

	def postprocess_response(self):
		'''
		Hook to allow custom subclasses to process responses.
		Usually will access self.json to get the full JSON record that created this entity.
		'''
		pass	

class WPRequest(metaclass=ABCMeta):
	'''
	Abstract superclass for WordPress requests.
	'''
	def __init__(self, api=None):
		
		if api is None:
			raise Exception("Create this object ('{}') from the API object, not directly.".format(self.__class__.__name__))
		
		self.api = api
		self.parameters = dict()
		self.response = None
		self._parameter_names = None

		for arg in self.parameter_names:
			setattr(self, arg, None)

		#self.context = "view" # default value
	
#	@property
#	def context(self):
#		# 'view' is default value in API
#		return self.arguments.get("context", "view")

	@abstractproperty
	def parameter_names(self):
		pass

	@abstractmethod
	def get(self):
		pass
		
	def get_response(self):
		if self.response is None:
			if self.api.session is None:
				print("creating new request")
				# no exiting request, create a new one
				self.response = requests.get(url=self.url, params=self.parameters, auth=self.api.auth())
			else:
				# use existing session
				self.response = self.api.session.get(url=self.url, params=self.parameters, auth=self.api.auth())
		self.response.raise_for_status()
		#return self.response
		
	@property
	def request(self):
		if self.response:
			return self.response.request
		else:
			return None
#		else:
#			return self.response.request

