
'''

WordPress API reference: https://developer.wordpress.org/rest-api/reference/posts/
'''

import json
import logging
import requests

from .wordpress_entity import WPEntity, WPRequest, context_values
#from .post import PostRequest
from ..import exc
from ..cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger(__name__.split(".")[0]) # package name

order_values = ["asc", "desc"]
orderby_values = ["id", "include", "name", "slug", "term_group", "description", "count"]

class Category(WPEntity):
	
	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)
		
		# cache related objects
		self._posts = None
		
	def __repr__(self):
		return "<WP {0} object at {1} name='{2}'>".format(self.__class__.__name__, hex(id(self)), self.s.name)
	
	@property
	def schema_fields(self):
		if self._schema_fields is None:
			# These are the default WordPress fields for the "category" object.
			self._schema_fields = ["id", "count", "description", "link", "name", "slug", "taxonomy", "parent", "meta"]
		return self._schema_fields
	
	@property
	def post_fields(self):
		'''
		Arguments for Category POST requests.
		'''
		if self._post_fields is None:
			self._post_fields = ["description", "name", "slug", "parent", "meta"]
		return self._post_fields

	def posts(self):
		'''
		Return a list of posts (type: Post) that have this category.
		'''
		# maybe not cache this...?
		if self._posts is None:
			pr = self.api.PostRequest()
			pr.categories.append(self)
			self._posts = pr.get()
		return self._posts


class CategoryRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress categories.
	'''
	def __init__(self, api=None):
		super().__init__(api=api)
		self.id = None # WordPress ID
		
		self.url = self.api.base_url + "categories"
		
		# parameters that undergo validation, i.e. need custom setter
		#
		self._hide_empty = None
		self._per_page = None
		
	@property
	def parameter_names(self):
		if self._parameter_names is None:
			self._parameter_names = ["context", "page", "per_page", "search", "exclude", "include",
									 "order", "orderby", "hide_empty", "parent", "post", "slug"]
		return self._parameter_names
	
	def populate_request_parameters(self):
		'''
		Populates 'self.parameters' to prepare for executing a request.
		'''
		if self.context:
			self.parameters["context"] = self.context
		else:
			self.parameters["context"] = "view" # default value

		for param in self.parameter_names:
			if getattr(self, param, None):
				self.parameters[param] = getattr(self, param)

	def get(self, class_object=Category, count=False, embed=True, links=True):
		'''
		Returns a list of 'Category' objects that match the parameters set in this object.

		class_object : the class of the objects to instantiate based on the response, used when implementing custom subclasses
		count        : BOOL, return the number of entities matching this request, not the objects themselves
		embed        : BOOL, if True, embed details on linked resources (e.g. URLs) instead of just an ID in response to reduce number of HTTPS calls needed,
			           see: https://developer.wordpress.org/rest-api/using-the-rest-api/linking-and-embedding/#embedding
		links        : BOOL, if True, returns with response a map of links to other API resources
		'''
		super().get(class_object=class_object, count=count, embed=embed, links=links)
		
		#if self.id:
		#	self.url += "/{}".format(self.id)

		self.populate_request_parameters()

		try:
			self.get_response(wpid=self.id)
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("Post response code: {}".format(self.response.status_code))
			if self.response.status_code == 400: # bad request
				logger.debug("URL={}".format(self.response.url))
				raise exc.BadRequest("400: Bad request. Error: \n{0}".format(json.dumps(self.response.json(), indent=4)))
			elif self.response.status_code == 404: # not found
				return None
			elif self.response.status_code == 500: # 
				raise Exception("500: Internal Server Error. Error: \n{0}".format(self.response.json()))
			raise Exception("Unhandled HTTP response, code {0}. Error: \n{1}\n".format(self.response.status_code, self.response.json()))
				
		self.process_response_headers()

		if count:
			# return just the number of objects that match this request
			if self.total is None:
				raise Exception("Header 'X-WP-Total' was not found.") # if you are getting this, modify to use len(posts_data)
			return self.total
			#return len(pages_data)

		categories_data = self.response.json()
		
		if isinstance(categories_data, dict):
			# only one object was returned, make it a list
			categories_data = [categories_data]
			
		categories = list()
		for d in categories_data:
			
			# Before we continue, do we have this Category in the cache already?
			try:
				logger.debug(d)
				category = self.api.wordpress_object_cache.get(class_object.__name__, key=d["id"]) # default = Category()
			except WPORMCacheObjectNotFoundError:
				category = class_object.__new__(class_object) # default = Category()
				category.__init__(api=self.api)
				category.json = json.dumps(d)
				
				category.update_schema_from_dictionary(d)
					
				if "_embedded" in d:
					logger.debug("TODO: implement _embedded content for Category object")
	
				# perform postprocessing for custom fields
				category.postprocess_response()
				
				# add to cache
				self.api.wordpress_object_cache.set(value=category, keys=(category.s.id, category.s.slug))
			finally:
				categories.append(category)
		
		return categories

	@property
	def context(self):
		if self._context is None:
			self._context = None
		return self._context
	
	@context.setter
	def context(self, value):
		if value is None:
			self._context =  None
			return
		else:
			try:
				value = value.lower()
				if value in ["view", "embed", "edit"]:
					self._context = value
					return
			except:
				pass
			raise ValueError ("'context' may only be one of ['view', 'embed', 'edit']")

	@property
	def order(self):
		return self._order;
		#return self.api_params.get('order', None)
		
	@order.setter
	def order(self, value):
		if value is None:
			self._order = None
		else:
			if isinstance(value, str):
				value = value.lower()
				if value not in order_values:
					raise ValueError('The "order" parameter must be one '+\
									 'of these values: {}'.format(order_values))
				else:
					#self.api_params['order'] = value
					self._order = value
			else:
				raise ValueError('The "order" parameter must be one of '+\
								 'these values: {} (or None).'.format(order_values))
		return self._order

	@property
	def orderby(self):
		return self.api_params.get('orderby', None)
		
	@orderby.setter
	def orderby(self, value):
		if value is None:
			self._orderby = None
		else:
			if isinstance(value, str):
				value = value.lower()
				if value not in orderby_values:
					raise ValueError('The "orderby" parameter must be one '+\
									 'of these values: {}'.format(orderby_values))
				else:
					#self.api_params['orderby'] = value
					self._orderby = value
			else:
				raise ValueError('The "orderby" parameter must be one of these '+\
								 'values: {} (or None).'.format(orderby_values))
		return self._orderby

	@property
	def hide_empty(self):
		return self._hide_empty
	
	@hide_empty.setter
	def hide_empty(self, value):
		if isinstance(value, bool) or value is None:
			self._hide_empty = value
		else:
			raise ValueError("The property 'hide_empty' must be a Boolean value "+\
							"('{0}' provided).".format(type(value)))

	@property
	def per_page(self):
		return self._per_page
	
	@per_page.setter
	def per_page(self, value):
		if value is None:
			if "per_page" in self.parameters:
				del self.parameters["per_page"]
				
		elif isinstance(value, str):
			try:
				value = int(value)
			except ValueError:
				raise ValueError("The 'per_page' parameter should be a number.")
			
		elif isinstance(value, int):
			if value < 0:
				raise ValueError("The 'per_page' parameter should greater than zero.")
			else:
				self._per_page = value
		
		else:
			raise ValueError("The 'per_page' parameter should be a number.")
	
	
