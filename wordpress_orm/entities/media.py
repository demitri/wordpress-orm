
'''

WordPress API reference: https://developer.wordpress.org/rest-api/reference/media/
'''

import os
import logging

import requests

from .wordpress_entity import WPEntity, WPRequest, context_values
from ..cache import WPORMCache, WPORMCacheObjectNotFoundError

logger = logging.getLogger("{}".format(__loader__.name.split(".")[0])) # package name

status_values = ["publish", "future", "draft", "pending", "private"]

class Media(WPEntity):

	def __init__(self, id=None, api=None):
		super().__init__(api=api)

		# related objects to cache
		self._author = None
		self._associated_post = None

	def __repr__(self):
		return "<WP {0} object at {1}, id={2}, type='{3}', file='{4}'>".format(self.__class__.__name__, hex(id(self)),
																			self.s.id,
																			self.s.mime_type,
																			os.path.basename(self.s.source_url))

	@property
	def schema_fields(self):
		if self._schema_fields is None:
			# These are the default WordPress fields for the "media" object.
			self._schema_fields = ["date", "date_gmt", "guid", "id", "link", "modified", "modified_gmt",
									"slug", "status", "type", "title", "author", "comment_status",
									"ping_status", "meta", "template", "alt_text", "caption", "description",
									"media_type", "mime_type", "media_details", "post", "source_url"]
		return self._schema_fields

	@property
	def media_type(self):
		'''
		The media type, one of ["image", "file"].
		'''
		return self.s.media_type

	@property
	def author(self):
		'''
		Returns the author of this post, class: 'User'.
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

	@property
	def post(self):
		'''
		The post associated with this media item.
		'''
		if self._associated_post is None:
			pr = self.api.PostRequest()
			pr.id = self.s.featured_media
			posts = pr.get()
			if len(media_list) == 1:
				self._associated_post = posts[0]
			else:
				self._associated_post = None
		return self._associated_post


class MediaRequest(WPRequest):
	'''
	'''

	def __init__(self, api=None):
		super().__init__(api=api)
		self.id = None # WordPress id

		# parameters that undergo validation, i.e. need custom setter
		# default values set here
		self._context = None #"view"
		self._page = None
		self._per_page = None

	@property
	def parameter_names(self):
		'''
		Media request parameters.
		'''
		if self._parameter_names is None:
			# parameter names defined by WordPress media query
			self._parameter_names = ["context", "page", "per_page", "search", "after", "author",
									"author_exclude", "before", "exclude", "include", "offset",
									"order", "orderby", "parent", "parent_exclude", "slug", "status",
									"media_type", "mime_type"]
		return self._parameter_names

	def get(self, classobject=Media):
		self.url = self.api.base_url + "media"

		if self.id:
			self.url += "/{}".format(self.id)

#		logger.debug("URL='{}'".format(self.url))

		# -------------------
		# populate parameters
		# -------------------
		if self.context:
			self.parameters["context"] = self.context
			request_context = self.context
		else:
			request_context = "view" # default value

		if self.page:
			self.parameters["page"] = self.page

		if self.per_page:
			self.parameters["per_page"] = self.per_page

		if self.search:
			assert False, "Field 'search' not yet implemented."

		if self.after:
			assert False, "Field 'after' not yet implemented."

		if self.author:
			assert False, "Field 'author' not yet implemented."

		if self.author_exclude:
			assert False, "Field 'author_exclude' not yet implemented."

		if self.before:
			assert False, "Field 'before' not yet implemented."

		if self.exclude:
			assert False, "Field 'exclude' not yet implemented."

		if self.include:
			assert False, "Field 'include' not yet implemented."

		if self.offset:
			assert False, "Field 'offset' not yet implemented."

		if self.order:
			assert False, "Field 'order' not yet implemented."

		if self.orderby:
			assert False, "Field 'orderby' not yet implemented."

		if self.parent:
			assert False, "Field 'parent' not yet implemented."

		if self.parent_exclude:
			assert False, "Field 'parent_exclude' not yet implemented."

		if self.slug:
			self.parameters["slug"] = self.slug

		if self.status:
			assert False, "Field 'status' not yet implemented."

		if self.media_type:
			assert False, "Field 'media_type' not yet implemented."

		if self.mime_type:
			assert False, "Field 'mime_type' not yet implemented."

		# -------------------

		try:
			self.get_response()
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("HTTP error! media response code: {}".format(self.response.status_code))
			if self.response.status_code == 404:
				return None
			elif self.response.status_code == 404:
				return None

		media_data = self.response.json()

		if isinstance(media_data, dict):
			# only one object was returned; make it a list
			media_data = [media_data]

		media_objects = list()
		for d in media_data:

			# Before we continue, do we have this Media in the cache already?
			try:
				media = self.api.wordpress_object_cache.get(class_name=Media.__name__, key=d["id"])
				media_objects.append(media)
				continue
			except WPORMCacheObjectNotFoundError:
				pass

			media = classobject.__new__(classobject)
			media.__init__(api=self.api)
			media.json = d

			# Properties applicable to 'view', 'edit', 'embed' query contexts
			#
			#logger.debug(d)
			media.s.date = d["date"]
			media.s.id = d["id"]
			media.s.link = d["link"]
			media.s.slug = d["slug"]
			media.s.type = d["type"]
			media.s.title = d["title"]
			media.s.author = d["author"]
			media.s.alt_text = d["alt_text"]
			media.s.caption = d["caption"]["rendered"]
			media.s.media_type = d["media_type"]
			media.s.mime_type = d["mime_type"]
			media.s.media_details = d["media_details"]
			media.s.source_url = d["source_url"]

			# Properties applicable only to 'view', 'edit' query contexts
			#
			if request_context in ["view", "edit"]:
				media.s.date_gmt = d["date_gmt"]
				media.s.guid = d["guid"]
				media.s.modified = d["modified"]
				media.s.modified_gmt = d["modified_gmt"]
				media.s.status = d["status"]
				media.s.comment_status = d["comment_status"]
				media.s.ping_status = d["ping_status"]
				media.s.meta = d["meta"]
				media.s.template = d["template"]
				media.s.description = d["description"]["rendered"]
				media.s.post = d["post"]

			# Allow postprocessing for custom fields
			media.postprocess_response()
			# add to cache
			self.api.wordpress_object_cache.set(class_name=Media.__name__, key=media.s.id, value=media)
			self.api.wordpress_object_cache.set(class_name=Media.__name__, key=media.s.slug, value=media)

			media_objects.append(media)

		return media_objects

	@property
	def context(self):
		return self._context

	@context.setter
	def context(self, value):
		if value is None:
			self._context = None
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
