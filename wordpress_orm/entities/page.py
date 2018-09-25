
'''

WordPress API reference: https://developer.wordpress.org/rest-api/reference/pages/
'''

import json
import logging
import requests
from datetime import datetime

from .wordpress_entity import WPEntity, WPRequest, context_values
from .user import User

from .. import exc
from ..cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger(__name__.split(".")[0]) # package name

order_values = ["asc", "desc"]
orderby_values = ["author", "date", "id", "include", "modified", "parent",
				  "relevance", "slug", "title", "menu_order"]

class Page(WPEntity):

	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)

		# related objects to cache
		self._author = None
		self._featured_media = None

	def __repr__(self):
		if len(self.s.title) < 11:
			truncated_title = self.s.title
		else:
			truncated_title = self.s.title[0:10] + "..."
		return "<WP {0} object at {1}, id={2}, title='{3}'>".format(self.__class__.__name__,
													 hex(id(self)), self.s.id, truncated_title)

	@property
	def schema_fields(self):
		if self._schema_fields is None:
			self._schema_fields = ["date", "date_gmt", "guid", "id", "link", "modified", "modified_gmt",
			   					   "slug", "status", "type", "password", "parent", "title", "content", "author",
			   					   "excerpt", "featured_media", "comment_status", "ping_status", "menu_order",
			   					   "meta", "template"]
		return self._schema_fields

	@property
	def post_fields(self):
		'''
		Arguments for POST requests.
		'''
		if self._post_fields is None:
			# Note that 'date' is excluded from the specification in favor of exclusive use of 'date_gmt'.
			self._post_fields = ["date_gmt", "slug", "status", "password", "parent", "title", "content",
								 "author", "excerpt", "featured_media", "comment_status", "ping_status",
								 "menu_order", "meta", "template"]
		return self._post_fields

	@property
	def featured_media(self):
		'''
		Returns the 'Media' object that is the "featured media" for this page.
		'''
		if self._featured_media is None:

			found_media = self.api.media(id=self.s.featured_media)
			self._featured_media = found_media

#			mr = self.api.MediaRequest()
#			mr.id = self.s.featured_media
#			media_list = mr.get()
#			if len(media_list) == 1:
#				self._featured_media = media_list[0]
#			else:
#				self._featured_media = None
		return self._featured_media

	@property
	def author(self):
		'''
		Returns the author of this page, class: 'User'.
		'''
		if self._author is None:
			ur = self.api.UserRequest()
			ur.id = self.s.author # ID for the author of the object
			user_list = ur.get()
			if len(user_list) == 1:
				self._author = user_list[0]
			else:
				raise exc.UserNotFound("User ID '{0}' not found.".format(self.author))
		return self._author

class PageRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress pages.
	'''
	def __init__(self, api=None, categories=None, slugs=None):
		super().__init__(api=api)
		self.id = None # WordPress ID

		self.url = self.api.base_url + "pages"

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

		self._status = list()
		self._author_ids = list()
		self._parent_ids = list()
		self._parent_exclude_ids = list()
		self._slugs = list()

		if slugs:
			self.slugs = slugs

	@property
	def parameter_names(self):
		'''
		Page request parameters.
		'''
		if self._parameter_names is None:
			self._parameter_names = ["context", "page", "per_page", "search", "after", "author",
									 "author_exclude", "before", "exclude", "include", "menu_order", "offset",
									 "order", "orderby", "parent", "parent_exclude", "slug", "status"]
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

		if self.after:
			self.parameters["after"] = self._after.isoformat()

		if len(self.author) > 0:
			# takes a list of author IDs
			self.parameters["author"] = ",".join(self.author)

		if len(self.status) > 0:
			self.parameters["status"] = ",".join(self.status)

		if self.slug:
			self.parameters["slug"] = self.slug

		if len(self.parent) > 0:
			self.parameters["parent"] = ",".join(self.parent)

		if len(self.parent_exclude) > 0:
			self.parameters["parent_exclude"] = ",".join(self.parent_exclude)

		if self.order:
			self.parameters["order"] = self.order

		if self.menu_order:
			self.parameters["menu_order"] = self.menu_order
	
	def get(self, class_object=Page, count=False, embed=True, links=True):
		'''
		Returns a list of 'Page' objects that match the parameters set in this object.

		class_object : the class of the objects to instantiate based on the response, used when implementing custom subclasses
		count        : BOOL, return the number of entities matching this request, not the objects themselves
		embed        : BOOL, if True, embed details on linked resources (e.g. URLs) instead of just an ID in response to reduce number of HTTPS calls needed,
			           see: https://developer.wordpress.org/rest-api/using-the-rest-api/linking-and-embedding/#embedding
		links        : BOOL, if True, returns with response a map of links to other API resources
		'''
		super().get(class_object=class_object, count=count, embed=embed, links=links)		

		#if self.id:
		#	self.url += "/{}".format(self.id)

		self.populate_request_parameters() # populates 'self.parameters'

		try:
			self.get_response(wpid=self.id)
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("page response code: {}".format(self.response.status_code))
			if self.response.status_code == 400: # bad request
				logger.debug("URL={}".format(self.response.url))
				raise exc.BadRequest("400: Bad request. Error: \n{0}".format(json.dumps(self.response.json(), indent=4)))
			elif self.response.status_code == 404: # not found
				return None
			raise Exception("Unhandled HTTP response, code {0}. Error: \n{1}\n".format(self.response.status_code, self.response.json()))

		self.process_response_headers()

		if count:
			# return just the number of objects that match this request
			if self.total is None:
				raise Exception("Header 'X-WP-Total' was not found.") # if you are getting this, modify to use len(posts_data)
			return self.total
			#return len(pages_data)

		pages_data = self.response.json()

		if isinstance(pages_data, dict):
			# only one object was returned; make it a list
			pages_data = [pages_data]

		pages = list()
		for d in pages_data:

			# Before we continue, do we have this page in the cache already?
			try:
				page = self.api.wordpress_object_cache.get(class_name=class_object.__name__, key=d["id"])
			except WPORMCacheObjectNotFoundError:
				# create new object
				page = class_object.__new__(class_object) # default = Page()
				page.__init__(api=self.api)
				page.json = json.dumps(d)
	
				page.update_schema_from_dictionary(d)
		
				if "_embedded" in d:
					logger.debug("TODO: implement _embedded content for Page object")
	
				# perform postprocessing for custom fields
				page.postprocess_response()
	
				# add to cache
				self.api.wordpress_object_cache.set(value=page, keys=(page.s.id, page.s.slug))
			finally:
				pages.append(page)
				
		return pages

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
				raise ValueError("The 'Page' parameter must be an integer, was given '{0}'".format(value))

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
	def author(self):
		#return self._author
		#return self.parameters.get("author", None)
		return self._author_ids

	@author.setter
	def author(self, value):
		'''
		Set author parameter for this request; stores WordPress user ID.
		'''
		author_id = None

		if value is None:
			self.parameters.pop("author", None) # remove key
			return
			#self.g = None

		elif isinstance(value, User):
			# a single user was given, replace any existing list with this one
			self._author_ids = list()
			author_id = value.s.id

		elif isinstance(value, int):
			# a single id was given, replace any existing list with this one
			self._author_ids = list()
			author_id = value # assuming WordPress ID
			#self.parameters["author"] = value
			#self._author = value

		elif isinstance(value, str):
			# is this string value the WordPress user ID?
			try:
				author_id = int(value)
			except ValueError:
				# nope, see if it's the username and get the User object
				try:
					user = self.api.user(username=value)
					author_id = user.s.id
				except exc.NoEntityFound:
					raise ValueError("Could not determine a user from the value: {0} (type {1})".format(value, type(value)))

		else:
			raise ValueError("Unexpected value type passed to 'author' (type: '{1}')".format(type(value)))

		assert author_id is not None, "could not determine author_id from value {0}".format(value)
		#self.parameters["author"].append(str(author_id))
		self._author_ids.append(author_id)

	@property
	def after(self):
		'''
		WordPress parameter to return pages after this date.
		'''
		return self._after

	@after.setter
	def after(self, value):
		'''
		Set the WordPress parameter to return pages after this date.
		'''
		# The stored format is a datetime object, even though WordPress requires
		# it to be ISO-8601.
		#
		if value is None:
			self.parameters.pop("after", None)
			self._after = None
		elif isinstance(value, datetime):
			self._after = value
		else:
			raise ValueError("Th 'after' property only accepts `datetime` objects.")

	@property
	def before(self):
		'''
		WordPress parameter to return pages before this date.
		'''
		return self._after

	@after.setter
	def before(self, value):
		'''
		Set the WordPress parameter to return pages before this date.
		'''
		# The stored format is a datetime object, even though WordPress requires
		# it to be ISO-8601.
		#
		if value is None:
			self.parameters.pop("before", None)
			self._before = None
		elif isinstance(value, datetime):
			self._before = value
		else:
			raise ValueError("The 'before' property only accepts `datetime` objects.")

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
	def status(self):
		return self._status

	@status.setter
	def status(self, value):
		'''

		Note that 'status' may contain one or more values.
		Ref: https://developer.wordpress.org/rest-api/reference/pages/#arguments
		'''
		if value is None:
			self.parameters.pop("status", None)
			self._status = list() # set default value
			return
		try:
			value = value.lower()
			if value in ["draft", "pending", "private", "publish", "future"]:
				# may be one or more values; store as a list
				if self._status:
					self._status.append(value)
				else:
					self._status = [value]
				return
		except:
			pass
		raise ValueError("'status' must be one of ['draft', 'pending', 'private', 'publish', 'future'] ('{0}' given)".format(value))

	@property
	def parent(self):
		return self._parent_ids

	@parent.setter
	def parent(self, values):
		'''
		This method validates the parent passed to this request.

		It accepts parent ID (integer or string) or the slug value.
		'''
		if values is None:
			self.parameters.pop("parent", None)
			self._parent_ids = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Parents must be provided as a list (or append to the existing list, or None).")

		for p in values:
			par_id = None
			if isinstance(p, int):
#				self._category_ids.append(str(c))
				par_id = p
			elif isinstance(p, str):
				try:
					# is this a category ID value?
					par_id = int(p)
					#self._category_ids.append(str(int(c)))
				except ValueError:
					# not a category ID value, try by slug?
					try:
						parent = self.api.category(slug=p)
						par_id = parent.s.id
						#self._category_ids.append(category.s.id)
					except exc.NoEntityFound:
						logger.debug("Asked to find a parent with the slug '{0}' but not found.".format(slug))

			# Categories are stored as string ID values.
			#
			self._parent_ids.append(str(par_id))

	@property
	def parent_exclude(self):
		return self._parent_exclude_ids

	@parent_exclude.setter
	def parent_exclude(self, values):
		'''
		This method validates the parent_exclude passed to this request.

		It accepts category ID (integer or string) or the slug value.
		'''
		if values is None:
			self.parameters.pop("parent_exclude", None)
			self._parent_exclude_ids = list()
			return
		elif not isinstance(values, list):
			raise ValueError("parent_exclude must be provided as a list (or append to the existing list, or None).")

		for p in values:
			par_id = None
			if isinstance(p, int):
#				self._category_exclude_ids.append(str(c))
				par_id = p
			elif isinstance(p, str):
				try:
					# is this a category ID value?
					par_id = int(p)
					#self._category_exclude_ids.append(str(int(c)))
				except ValueError:
					# not a category ID value, try by slug?
					try:
						category = self.api.parent(slug=p)
						par_id = parent.s.id
						#self._category_exclude_ids.append(category.s.id)
					except exc.NoEntityFound:
						logger.debug("Asked to find a parent with the slug '{0}' but not found.".format(slug))

			# Categories are stored as string ID values.
			#
			self._parent_exclude_ids.append(str(par_id))

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
