'''

WordPress API reference: https://developer.wordpress.org/rest-api/reference/posts/
'''

import json
import logging
import requests

from .wordpress_entity import WPEntity, WPRequest, context_values
from ..cache import WPORMCacheObjectNotFoundError
from ..exc import AuthenticationRequired, MissingRequiredParameter

logger = logging.getLogger(__name__.split(".")[0]) # package name

class User(WPEntity):
	
	def __init__(self, id=None, session=None, api=None, from_dictionary=None):
		super().__init__(api=api)
		
		# parameters that undergo validation, i.e. need custom setter
		self._context = None

		# cache related objects
		self._posts = None			
		
	@property
	def schema_fields(self):
		if self._schema_fields is None:
			# These are the default WordPress fields for the "user" object.
			self._schema_fields = ["id", "username", "name", "first_name", "last_name", "email", "url",
				   "description", "link", "locale", "nickname", "slug", "registered_date",
				   "roles", "password", "capabilities", "extra_capabilities", "avatar_urls", "meta"]
		return self._schema_fields

	@property
	def post_fields(self):
		if self._post_fields is None:
			self._post_fields = ["username", "name", "first_name", "last_name", "email", "url", 
								 "description", "locale", "nickname", "slug", "roles", "password", "meta"]
		return self._post_fields

	def commit(self):
		'''
		Creates a new user or updates an existing user via the API.
		'''
		# is this a new user?
		new_user = (self.s.id is None)
		
		post_fields = ["username", "name", "first_name", "last_name", "email", "url",
					   "description", "locale", "nickname", "slug", "roles", "password", "meta"]
		if new_user:
			post_fields.append("id")
		
		parameters = dict()
		for field in post_fields:
			if getattr(self.s, field) is not None:
				parameters[field] = getattr(self.s, field)
		
		# new user validation
		if new_user:
			required_fields = ["username", "email", "password"]
			for field in required_fields:
				if getattr(self.s, field) is None:
					raise MissingRequiredParameter("The '{0}' field must be provided when creating a new user.".format(field))
		
		response = self.api.session.post(url=self.url, params=parameters, auth=self.api.auth())
				
		return response

	@property
	def posts(self):
		if self._posts is None:
			pr = self.api.PostRequest()
			pr.author = self
			self._posts = pr.get()
		return self._posts

	def __repr__(self):
		return "<WP {0} object at {1}, id={2}, name='{3}'>".format(self.__class__.__name__, hex(id(self)), self.s.id, self.s.name)
	
	def gravatar_url(self, size=200, rating='g', default_image_style="mm"):
		'''
		Returns a URL to the Gravatar image associated with the user's email address.
		
		Ref: https://en.gravatar.com/site/implement/images/
		
		size: int, can be anything from 1 to 2048 px
		rating: str, maximum rating of the image, one of ['g', 'pg', 'r', 'x']
		default_image: str, type of image if gravatar image doesn't exist, one of ['404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash', 'blank']
		'''
		if rating not in ['g', 'pg', 'r', 'x']:
			raise ValueError("The gravatar max rating must be one of ['g', 'pg', 'r', 'x'].")
		
		if default_image_style not in ['404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash', 'blank']:
			raise ValueError("The gravatar default image style must be one of ['404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro', 'robohash', 'blank'].")			
		
		if not isinstance(size, int):
			try:
				size = int(size)
			except ValueError:
				raise ValueError("The size parameter must be an integer value between 1 and 2048.")
		
		if isinstance(size, int):
			if 1 <= size <= 2048:
				#
				# self.s.avatar_urls is a dictionary with key=size and value=URL.
				# Sizes are predetermined, but not documented. Values found were ['24', '48', '96'].
				#
				grav_urls_dict = self.s.avatar_urls
				grav_url = grav_urls_dict[list(grav_urls_dict)[0]] # get any URL (we'll set our own size) / list(d) returns list of dictionary's keys
				grav_url_base = grav_url.split("?")[0]
				params = list()
				params.append("d={0}".format(default_image_style)) # set default image to 'mystery man'
				params.append("r={0}".format(rating)) # set max rating to 'g'
				params.append("s={0}".format(size))
				
				return "{0}?{1}".format(grav_url_base, "&".join(params))
		else:
			raise ValueError("The size parameter must be an integer.")
		
	@property
	def fullname(self):
		return "{0} {1}".format(self.s.first_name, self.s.last_name)
	

class UserRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress users.
	'''
	def __init__(self, api=None):
		super().__init__(api=api)
		self.id = None # WordPress ID
		
		self.url = self.api.base_url + 'users'
		
		# values from headers
		self.total = None
		self.total_pages = None
		
		self._page = None
		self._per_page = None
		self._offset = None
		self._order = None
		self._orderby = None
		
		# parameters that undergo validation, i.e. need custom setter
		self._includes = list()
		self._slugs = list() # can accept more than one
		self._roles = list()
				
	@property
	def parameter_names(self):
		if self._parameter_names is None:
			# parameter names defined by WordPress user query
			self._parameter_names = ["context", "page", "per_page", "search", "exclude",
									 "include", "offset", "order", "orderby", "slug", "roles"]
		return self._parameter_names
	
	def populate_request_parameters(self):
		'''
		Populates 'self.parameters' to prepare for executing a request.
		'''
		if self.context:
			self.parameters["context"] = self.context
		else:
			self.parameters["context"] = "view" # default value

		if self.page:
			self.parameters["page"] = self.page
		
		if self.per_page:
			self.parameters["per_page"] = self.per_page

		if self.search:
			self.parameters["search"] = self.search

		# exclude : Ensure result set excludes specific IDs.
		if self.search:
			self.parameters["exclude"] = self.search

		# include : Limit result set to specific IDs.
		if len(self._includes) > 0:
			self.parameters["include"] = ",".join.self.includes
			
		# offset : Offset the result set by a specific number of items.
		if self.offset:
			self.parameters["offset"] = self.search
		
		# order : Order sort attribute ascending or descending, default "asc", one of ["asc", "desc"]
		if self.order:
			self.parameters["order"] = self.order
		
		# orderby : Sort collection by object attribute.
		if self.orderby:
			self.parameters["orderby"] = self.orderby

		# slug : Limit result set to users with one or more specific slugs.
		if len(self.slug) > 0:
			self.parameters["slug"] = ",".join(self.slug)
		
		# roles : Limit result set to users matching at least one specific role provided. Accepts csv list or single role.
		if len(self.roles) > 0:
			self.parameters["roles"] = ",".join(self.roles)

	def get(self, class_object=User, count=False, embed=True, links=True):
		'''
		Returns a list of 'Tag' objects that match the parameters set in this object.
		
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
			logger.debug("User response code: {}".format(self.response.status_code))
			if 400 < self.response.status_code < 499:
				if self.response.status_code in [401, 403]: # 401 = Unauthorized, 403 = Forbidden
					data = self.response.json()
					if data["code"] == 'rest_user_cannot_view':
						# TODO: write more detailed message and propose solution
						raise AuthenticationRequired("WordPress authentication is required for this operation. Response: {0}".format(data))
					raise AuthenticationRequired("WordPress authentication is required for this operation. Response: {0}".format(data))
#				elif self.response.status_code == 404:
#					return None
			raise Exception("Unhandled HTTP response, code {0}. Error: \n{1}\n".format(self.response.status_code, self.response.json()))

		self.process_response_headers()
	
		if count:
			# return just the number of objects that match this request
			if self.total is None:
				raise Exception("Header 'X-WP-Total' was not found.") # if you are getting this, modify to use len(posts_data)
			return self.total
	
		users_data = self.response.json()
		
		if isinstance(users_data, dict):
			# only one object was returned; make it a list
			users_data = [users_data]
	
		users = list()
		for d in users_data:

			# Before we continue, do we have this User in the cache already?
			try:
				user = self.api.wordpress_object_cache.get(class_name=class_object.__name__, key=d["id"])
			except WPORMCacheObjectNotFoundError:
				user = class_object.__new__(class_object)
				user.__init__(api=self.api)
				user.json = json.dumps(d)
				
				user.update_schema_from_dictionary(d)
				
				if "_embedded" in d:
					logger.debug("TODO: implement _embedded content for User object")
	
				# perform postprocessing for custom fields
				user.postprocess_response()
				
				# add to cache
				self.api.wordpress_object_cache.set(value=user, keys=(user.s.id, user.s.slug))
			finally:
				users.append(user)

		return users

	# ================================= query properties ==============================
	
	@property
	def context(self):
		return self._context
	
	@context.setter
	def context(self, value):
		if value is None:
			self._context = None
			return
		else:
			try:
				value = value.lower()
				if value in ["view", "embed", "edit"]:
					self._context = value
					return
			except:
				pass
		raise ValueError ("'context' may only be one of ['view', 'embed', 'edit'] ('{0}' given)".format(value))
				
	@property
	def page(self):
		'''
		Current page of the collection.
		'''
		return self._page
		
	@page.setter
	def page(self, value):
		#
		# only accept integers or strings that can become integers
		#
		if isinstance(value, int):
			self._page = value
		elif isinstance(value, str):
			try:
				self._page = int(value)
			except ValueError:
				raise ValueError("The 'page' parameter must be an integer, was given '{0}'".format(value))

	@property
	def per_page(self):
		'''
		Maximum number of items to be returned in result set.
		'''
		return self._per_page
		
	@per_page.setter
	def per_page(self, value):
		# only accept integers or strings that can become integers
		#
		if isinstance(value, int):
			self._per_page = value
		elif isinstance(value, str):
			try:
				self._per_page = int(value)
			except ValueError:
				raise ValueError("The 'per_page' parameter must be an integer, was given '{0}'".format(value))

	@property
	def include(self):
		return self._includes

	@include.setter
	def include(self, values):
		'''
		Limit result set to specified WordPress user IDs, provided as a list.
		'''
		if values is None:
			self.parameters.pop("include", None)
			self._includes = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Includes must be provided as a list (or append to the existing list).")
		
		for inc in values:
			if isinstance(inc, int):
				self._includes.append(str(inc))
			elif isinstance(inc, str):
				try:
					self._includes.append(str(int(inc)))
				except ValueError:
					raise ValueError("The WordPress ID (an integer, '{0}' given) must be provided to limit result to specific users.".format(inc))

	@property
	def offset(self):
		return self._offset
		
	@offset.setter
	def offset(self, value):
		'''
		Set value to offset the result set by the specified number of items.
		'''
		if value is None:
			self.parameters.pop("offset", None)
			self._offset = None
		elif isinstance(value, int):
			self._offset = value
		elif isinstance(value, str):
			try:
				self._offset = str(int(str))
			except ValueError:
				raise ValueError("The 'offset' value should be an integer, was given: '{0}'.".format(value))

	@property
	def order(self):
		return self._order;
		#return self.api_params.get('order', None)
		
	@order.setter
	def order(self, value):
		if value is None:
			self.parameters.pop("order", None)
			self._order = None
		else:
			order_values = ['asc', 'desc']
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
		return self._orderby #api_params.get('orderby', None)
		
	@orderby.setter
	def orderby(self, value):
		if value is None:
			self.parameters.pop("orderby", None)
			self._orderby = None
		else:
			order_values = ['asc', 'desc']
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
	def slug(self):
		return self._slugs
	
	@slug.setter
	def slug(self, value):
		if value is None:
			self._slugs = list()
		elif isinstance(value, str):
			self._slugs.append(value)
		elif isinstance(value, list):
			# validate data type
			for v in value:
				if not isinstance(v, str):
					raise ValueError("slugs must be string type; found '{0}'".format(type(v)))
			self._slugs = value

	@property
	def roles(self):
		'''
		User roles to be used in query.
		'''
		return self._roles
		
	@roles.setter
	def roles(self, values):
		if values is None:
			self.parameters.pop("roles", None)
			self._roles = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Roles must be provided as a list (or append to the existing list).")
		
		for role in values:
			if isinstance(role, str):
				self.roles.append(role)
			else:
				raise ValueError("Unexpected type for property list 'roles'; expected str, got '{0}'".format(type(s)))
			
