'''
WordPress API reference: https://developer.wordpress.org/rest-api/reference/comments/
'''

import json
import logging
import requests

from .wordpress_entity import WPEntity, WPRequest, context_values
from .post import Post
from ..import exc
from ..cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger(__name__.split(".")[0]) # package name

order_values = ["asc", "desc"]
orderby_values = ["date", "date_gmt", "id", "include", "post", "parent", "type"]

# -

class Comment(WPEntity):
	
	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)
	
		# cache related objects
		self._author = None
	
	def __repr__(self):
		if len(self.s.content) < 11:
			truncated_content = self.s.content
		else:
			truncated_content = self.s.content[0:10] + "..."
		return "<WP {0} object at {1} content='{2}'>".format(self.__class__.__name__, hex(id(self)), truncated_content)
	
	@property
	def schema_fields(self):
		if self._schema_fields is None:
			self._schema_fields = ["id", "author", "author_email", "author_ip", "author_name",
								   "author_url", "author_user_agent", "content", "date",
								   "date_gmt", "link", "parent", "post", "status", "type",
								   "author_avatar_urls", "meta"]
		return self._schema_fields
	
	@property
	def post_fields(self):
		'''
		Arguments for POST requests.
		'''
		if self._post_fields is None:
			# Note that 'date' is excluded from the specification in favor of exclusive use of 'date_gmt'.
			self._post_fields = ["author", "author_email", "author_ip", "author_name", "author_url",
								 "author_user_agent", "content", "date_gmt", "parent", "post", "status", "meta"]
		return self._post_fields

	def author(self):
		'''
		Return the WordPress User object that wrote this comment, if it was a WP User, None otherwise.
		'''
		if self._author is None:
			ur = self.api.UserRequest()
			ur.id = self.s.author # 'author' field is user ID
			users = ur.get()
			if len(users) > 0:
				self._author = users[0]
			else:
				self._author = None
		return self._author

class CommentRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress comments.
	'''

	def __init__(self, api=None, post=None):
		super().__init__(api=api)
		self.id = None # WordPress ID
		
		self.url = self.api.base_url + "comments"
		
		self._context = None
		self._posts = list()

		if post:
			# initializer takes one; set the property manually to set several
			self.posts = [post]
		
		# parameters that undergo validation, i.e. need custom setter
		#
		# ...
		
	@property
	def parameter_names(self):
		if self._parameter_names is None:
			self._parameter_names = ["context ", "page", "per_page", "search", "after", "author",
				"author_exclude", "author_email", "before", "exclude", "include",
				"offset", "order", "orderby", "parent", "parent_exclude", "post",
				"status", "type", "password"]
		return self._parameter_names
	
	def populate_request_parameters(self):
		'''
		Populates 'self.parameters' to prepare for executing a request.
		'''
		if self.context:
			self.parameters["context"] = self.context
		else:
			self.parameters["context"] = "view" # default value
		
		if self.password:
			self.parameters["password"] = self.password
			
		if len(self.posts) > 0:
			logger.debug("Posts: {0}".format(self.posts))
			self.parameters["post"] = ",".join(self.posts) # post ID

	def get(self, class_object=Comment, count=False, embed=True, links=True):
		'''
		Returns a list of 'Comment' objects that match the parameters set in this object.

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
			logger.debug("URL='{}'".format(self.request.url))
			self.get_response(wpid=self.id)
		except requests.exceptions.HTTPError:
			logger.debug("Post response code: {}".format(self.response.status_code))
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

		comments_data = self.response.json()
		
		if isinstance(comments_data, dict):
			# only one object was returned, make it a list
			comments_data = [comments_data]
			
		comments = list()
		for d in comments_data:

			# Before we continue, do we have this Comment in the cache already?
			try:
				comment = self.api.wordpress_object_cache.get(class_name=class_object.__name__, key=d["id"])
			except WPORMCacheObjectNotFoundError:
				# create new object
				comment = class_object.__new__(class_object) # default = Comment()
				comment.__init__(api=self.api)
				comment.json = json.dumps(d)
				
				comment.update_schema_from_dictionary(d)
					
				if "_embedded" in d:
					logger.debug("TODO: implement _embedded content for Comment object")
	
				# perform postprocessing for custom fields
				comment.postprocess_response()
	
				# add to cache
				self.api.wordpress_object_cache.set(value=comment, keys=(comment.s.id, comment.s.slug))
			finally:
				comments.append(comment)
		
		return comments
		
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
	def posts(self):
		'''
		The list of posts (IDs) to retrieve the comments for.
		'''
		return self._posts
		
	@posts.setter
	def posts(self, values):
		'''
		Set the list of posts to retrieve comments for.
		'''
		
		# internally save the post ID.
		
		if values is None:
			self._posts = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Posts must be provided as a list (or append to the existing list).")

		for p in values:
			post_id = None
			if isinstance(p, Post):
				post_id = p.s.id
			elif isinstance(p, int):
				post_id = p
			elif isinstance(p, str):
				try:
					post_id = int(p)
				except ValueError:
					raise ValueError("Posts must be provided as a list of (or append to the existing list). Accepts 'Post' objects or Post IDs.")
			self._posts.append(str(post_id))



