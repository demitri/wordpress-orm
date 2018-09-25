
import inspect
import logging
from abc import ABCMeta, abstractmethod, abstractproperty

import requests

logger = logging.getLogger(__name__.split(".")[0]) # package name

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
			raise Exception("Use the 'wordpress_orm.API.{0}()' method to create a new '{0}' object (or set the 'api' parameter).".format(self.__class__.__name__))
		
		self.api = api			   # holds the connection information
		self.json = None		   # holds the raw JSON returned from the API
		self.s = WPSchema()		   # an empty object to use to hold custom properties
		self._schema_fields = None # a list of the fields in the schema
		self._post_fields = None   # a list of the fields used in POST queries

		# define the schema properties for the WPSchema object
		for field in self.schema_fields:
			setattr(self.s, field, None)
		
		# POST fields are also implemented as schema properties
		for field in self.post_fields:
			setattr(self.s, field, None)
				
	@abstractproperty
	def schema_fields(self):
		'''
		This method returns a list of schema properties for this entity, e.g. ["id", "date", "slug", ...]
		'''
		pass

	@abstractproperty
	def post_fields(self):
		'''
		This method returns a list of properties for creating (POSTing) a new entity to WordPress, e.g. ["date", "slug", ...]
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

	def postprocess_response(self, data=None):
		'''
		Hook to allow custom subclasses to process responses.
		Usually will access self.json to get the full JSON record that created this entity.
		'''
		pass
		
	def post(self, url=None, parameters=None, data=None):
		'''
		Implementation of HTTP POST comment for WordPress entities.
		'''
		if self.api.session is None:
			self.post_response = requests.post(url=url, data=data, params=parameters, auth=self.api.auth())
		else:
			# use existing session
			self.post_response = self.api.session.post(url=url, data=data, params=parameters, auth=self.api.auth())
		self.post_response.raise_for_status()

	def preprocess_additional_post_fields(self, data=None, parameters=None):
		'''
		Hook for subclasses to allow for custom processing of POST request data (before the request is made).
		'''
		pass
			
	def update_schema_from_dictionary(self, d, process_links=False):
		'''
		Replaces schema values with those found in provided dictionary whose keys match the field names.
		
		This is useful to parse the JSON dictionary returned by the WordPress API or embedded content
		(see: https://developer.wordpress.org/rest-api/using-the-rest-api/linking-and-embedding/#embedding).
		
		d : dictionary of data, key=schema field, value=data
		process_links : parse the values under the "_links" key, if present
		'''
		if d is None or not isinstance(d, dict):
			raise ValueError("The method 'update_schema_from_dictionary' expects a dictionary.")
		
		fields = self.schema_fields
		
		for key in fields:
			if key in d:
				if isinstance(d[key], dict) and "rendered" in d[key]:
					# for some fields, we want the "rendered" value - any cases where we don't??
					setattr(self.s, key, d[key]["rendered"])
				else:
					setattr(self.s, key, d[key])
			if key not in fields:
				logger.debug("WARNING: encountered field ('{0}') in dictionary that is not in the list of schema fields for '{1}' (fields: {2}).".format(key, self.__class__.__name__, fields))
		
		if process_links:
			# TODO: handle _links if present
			raise NotImplementedError("Processing '_links' has not yet been implemented.")

class WPRequest(metaclass=ABCMeta):
	'''
	Abstract superclass for WordPress requests.
	'''
	def __init__(self, api=None):
		
		if api is None:
			raise Exception("Create this object ('{0}') from the API object, not directly.".format(self.__class__.__name__))
		
		# WordPress headers ('X-WP-*')
		self.total = None		# X-WP-Total
		self.total_pages = None # X-WP-TotalPages
		self.nonce = None		# X-WP-Nonce
		
		self.api = api
		self.url = None
		self.parameters = dict()
		self.context = None		# parameter found on all entities
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

	def get(self, class_object=None, count=False, embed=True, links=True):
		'''
		Base implementation of the HTTP GET request to fetch WordPress entities.
		
		class_object : the class of the objects to instantiate based on the response, used when implementing custom subclasses
		count        : BOOL, return the number of entities matching this request, not the objects themselves
		embed        : BOOL, if True, embed details on linked resources (e.g. URLs) instead of just an ID in response to reduce number of HTTPS calls needed,
			           see: https://developer.wordpress.org/rest-api/using-the-rest-api/linking-and-embedding/#embedding
		links        : BOOL, if True, returns with response a map of links to other API resources
		'''
		if embed is True:
			self.parameters["_embed"] = "true"
		if links is True:
			self.parameters["_links"] = "true"
			
		if count:
			request_context = "embed" # only counting results, this is a shorter response
		else:
			request_context = "view" # default value
			
		# if the user set the 
	
	def process_response_headers(self):
		'''
		Handle any customization of parsing response headers, processes X-WP-* headers by default.
		'''
		# read response headers
		# ---------------------
		
		# Pagination, ref: https://developer.wordpress.org/rest-api/using-the-rest-api/pagination/
		#
		# X-WP-Total      : total number of records in the collection
		# X-WP-TotalPages : total number of pages encompassing all available records
		#
		if 'X-WP-Total' in self.response.headers:
			self.total = int(self.response.headers['X-WP-Total'])
		if 'X-WP-TotalPages' in self.response.headers:
			self.total_pages = int(self.response.headers['X-WP-TotalPages'])
			
		if 'X-WP-Nonce' in self.response.headers:
			self.nonce = self.response.headers['X-WP-Nonce']
	
	def get_response(self, wpid=None):
		'''
		
		wpid : specify this if a specific WordPress object (of given ID) is being requested
		'''
		if self.response is None:
		
			if wpid is None:
				url = self.url
			else:
				url = "{0}/{1}".format(self.url, wpid)
		
			if self.api.session is None:
				#logger.debug("creating new request")
				# no exiting request, create a new one
				self.response = requests.get(url=url, params=self.parameters, auth=self.api.auth())
			else:
				# use existing session
				self.response = self.api.session.get(url=url, params=self.parameters, auth=self.api.auth())
		self.response.raise_for_status()
		#return self.response
		
	@property
	def request(self):
		if self.response:
			return self.response.request
		else:
			return None

