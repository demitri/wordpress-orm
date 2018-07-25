
'''

WordPress API reference: https://developer.wordpress.org/rest-api/reference/tags/
'''

import json
import logging
import requests
from datetime import datetime

from .wordpress_entity import WPEntity, WPRequest, context_values

from .. import exc
from ..cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger("{}".format(__loader__.name.split(".")[0])) # package name

order_values = ["asc", "desc"]
orderby_values = ["id", "include", "name", "slug",
				  "term_group", "description", "count"]

class Tag(WPEntity):

	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)

	def __repr__(self):
		# if len(self.s.name) < 11:
		# 	truncated_name = self.s.name
		# else:
		# 	truncated_name = self.s.name[0:10] + "..."
		return "<WP {0} object at {1}, id={2}, name='{3}'>".format(self.__class__.__name__,
													 hex(id(self)), self.s.id, self.s.slug)

	@property
	def schema_fields(self):
		return ["id", "count", "description", "link",
			   "name", "slug", "taxonomy", "meta"]

class TagRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress tags.
	'''
	def __init__(self, api=None, categories=None, slugs=None):
		super().__init__(api=api)
		self.id = None # WordPress ID

		# values read from the response header
		self.total = None
		self.total_pages = None

		# parameters that undergo validation, i.e. need custom setter
		#self._author = None
		self._after = None
		self._before = None
		self._order = None
		self._orderby = None
		self._page = None
		self._per_page = None

		self._slugs = list()

		if slugs:
			self.slugs = slugs

	@property
	def parameter_names(self):
		'''
		Page request parameters.
		'''
		return ["context", "page", "per_page", "search", "exclude", "include", "offset",
				"order", "orderby", "hide_empty", "post", "slug"]

	def get(self, classobject=Tag, count=False):
		'''
		Returns a list of 'Tag' objects that match the parameters set in this object.

		count : Boolean, if True, only returns the number of object found.

		'''
		self.url = self.api.base_url + "tags"

		if self.id:
			self.url += "/{}".format(self.id)

		# -------------------
		# populate parameters
		# -------------------
		if self.context:
			self.parameters["context"] = self.context
			request_context = self.context
		else:
			if count:
				request_context = "embed" # only counting results, this is a shorter response
			else:
				request_context = "view" # default value

		if self.page:
			self.parameters["page"] = self.page

		if self.per_page:
			self.parameters["per_page"] = self.per_page

		if self.search:
			self.parameters["search"] = self.search

		if self.exclude:
			self.parameters["exclude"] = self.tags_exclude

		if self.include:
			self.parameters["include"] = self.include

		if self.offset:
			self.parameters["offset"] = self.offset

		if self.post:
			self.parameters["post"] = self.post

		if self.hide_empty:
			self.parameters["hide_empty"] = self.hide_empty

		if self.slug:
			self.parameters["slug"] = self.slug

		if self.order:
			self.parameters["order"] = self.order
		# -------------------

		try:
			self.get_response()
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("page response code: {}".format(self.response.status_code))
			if self.response.status_code == 400: # bad request
				logger.debug("URL={}".format(self.response.url))
				raise exc.BadRequest("400: Bad request. Error: \n{0}".format(json.dumps(self.response.json(), indent=4)))
			elif self.response.status_code == 404: # not found
				return None
			raise Exception("Unhandled HTTP response, code {0}. Error: \n{1}\n".format(self.response.status_code, self.response.json()))
			
		# read response headers
		self.total = self.response.headers['X-WP-Total']
		self.total_pages = self.response.headers['X-WP-TotalPages']

		tags_data = self.response.json()

		if isinstance(tags_data, dict):
			# only one object was returned; make it a list
			tags_data = [tags_data]

		if count:
			return len(tags_data)

		tags = list()
		for d in tags_data:

			# Before we continue, do we have this page in the cache already?
			try:
				tag = self.api.wordpress_object_cache.get(class_name=classobject.__name__, key=d["id"])
				tags.append(tag)
				continue
			except WPORMCacheObjectNotFoundError:
				pass

			tag = classobject.__new__(classobject)
			tag.__init__(api=self.api)
			tag.json = json.dumps(d)

			tag.update_schema_from_dictionary(d)

			# Properties applicable to 'view', 'edit', 'embed' query contexts
			#
# 			tag.s.id = d["id"]
# 			tag.s.link = d["link"]
# 			tag.s.slug = d["slug"]
# 			tag.s.taxonomy = d["taxonomy"]

			# Properties applicable to only 'view', 'edit' query contexts:
			#
# 			if request_context in ["view", "edit"]:
# #				view_edit_properties = ["date_gmt", "guid", "modified", "modified_gmt", "status",
# #										"content", "comment_status", "ping_status", "format", "meta",
# #										"sticky", "template", "categories", "tags"]
# #				for key in view_edit_properties:
# #					setattr(page.s, key, d[key])
# 				tag.s.count = d["count"]
# 				tag.s.description = d["description"]
# 				tag.s.meta = d["meta"]

			if "_embedded" in d:
				logger.debug("TODO: implement _embedded content for Tag object")
				
			slug.postprocess_response()
			
			# add to cache
			self.api.wordpress_object_cache.set(value=tag, keys=(tag.s.id, tag.s.slug))

			tags.append(tag)

		return tags

	@property
	def context(self):
		if self._context is None:
			self._context = None
		return self._context

	@context.setter
	def context(self, value):
		if value is None:
			self.parameters.pop("context", None)
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
	def order(self):
		return self._order;
		#return self.api_params.get('order', None)

	@order.setter
	def order(self, value):
		if value is None:
			self.parameters.pop("order", None)
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
			self.parameters.pop("orderby", None)
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
	def slugs(self):
		'''
		The list of page slugs to retrieve.
		'''
		return self._slugs

	@slugs.setter
	def slugs(self, values):
		if values is None:
			self.parameters.pop("slugs", None)
			self._slugs = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Slugs must be provided as a list (or append to the existing list).")

		for s in values:
			if isinstance(s, str):
				self._slugs.append(s)
			else:
				raise ValueError("Unexpected type for property list 'slugs'; expected str, got '{0}'".format(type(s)))
