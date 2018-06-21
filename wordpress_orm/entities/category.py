
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

logger = logging.getLogger("{}".format(__loader__.name.split(".")[0])) # package name

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
			self._schema_fields = ["id", "count", "description", "link",
									"name", "slug", "taxonomy", "parent", "meta"]
		return self._schema_fields

	# Pass-through properties
	# -----------------------
# 	@property
# 	def id(self):
# 		return self.s.id
#
# 	@property
# 	def count(self):
# 		return self.s.count
#
# 	@property
# 	def description(self):
# 		return self.s.description
#
# 	@property
# 	def link(self):
# 		return self.s.link
#
# 	@property
# 	def name(self):
# 		return self.s.name
#
# 	@property
# 	def slug(self):
# 		return self.s.slug
#
# 	@property
# 	def taxonomy(self):
# 		return self.s.taxonomy
#
# 	@property
# 	def parent(self):
# 		return self.s.parent
#
# 	@property
# 	def meta(self):
# 		return self.s.meta


	def posts(self):
		'''
		Return a list of posts (type: Post) that have this category.
		'''
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

		# parameters that undergo validation, i.e. need custom setter
		#
		self._hide_empty = None
		self._per_page = None

	@property
	def parameter_names(self):
		'''
		Category request parameters.
		'''
		if self._parameter_names is None:
			# parameter names defined by WordPress category query
			self._parameter_names = ["context", "page", "per_page", "search", "exclude", "include",
									"order", "orderby", "hide_empty", "parent", "post", "slug"]
		return self._parameter_names

	def get(self, classobject=Category):
		'''
		Returns a list of 'Categorie' objects that match the parameters set in this object.
		'''
		self.url = self.api.base_url + "categories"

		if self.id:
			self.url += "/{}".format(self.id)

		# populate parameters
		#
		if self.context:
			self.parameters["context"] = self.context
			request_context = self.context
		else:
			request_context = "view" # default value

		# populate parameters
		#
		for param in self.parameter_names:
			if getattr(self, param, None):
				self.parameters[param] = getattr(self, param)

		try:
			self.get_response()
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("Post response code: {}".format(self.response.status_code))
			if self.response.status_code == 400: # bad request
				logger.debug("URL={}".format(self.response.url))
				raise exc.BadRequest("400: Bad request. Error: \n{0}".format(json.dumps(self.response.json(), indent=4)))
			elif self.response.status_code == 404: # not found
				return None

		categories_data = self.response.json()

		if isinstance(categories_data, dict):
			# only one object was returned, make it a list
			categories_data = [categories_data]

		categories = list()
		for d in categories_data:

			# Before we continue, do we have this Category in the cache already?
			try:
				category = self.api.wordpress_object_cache.get(Category.__name__, key=d["id"])
				categories.append(category)
				continue
			except WPORMCacheObjectNotFoundError:
				pass

			category = classobject.__new__(classobject)
			category.__init__(api=self.api)
			category.json = d

			# Properties applicable to 'view', 'edit', 'embed' query contexts
			#
			category.s.id = d["id"]
			category.s.link = d["link"]
			category.s.name = d["name"]
			category.s.slug = d["slug"]
			category.s.taxonomy = d["taxonomy"]

			# Properties applicable to only 'view', 'edit' query contexts:
			#
			if request_context in ["view", "edit"]:
				category.s.count = d["count"]
				category.s.description = d["description"]
				category.s.parent = d["parent"]
				category.s.meta = d["meta"]

			# Allow postprocessing for custom fields
			category.postprocess_response()
			# add to cache
			self.api.wordpress_object_cache.set(class_name=Category.__name__, key=category.s.id, value=category)
			self.api.wordpress_object_cache.set(class_name=Category.__name__, key=category.s.slug, value=category)

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
