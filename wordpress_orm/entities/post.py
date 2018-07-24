                                                                                                                                                                                                                                                                                                                                                                                                                                                       
'''
WordPress API reference: https://developer.wordpress.org/rest-api/reference/posts/
'''

import json
import logging
import requests
from datetime import datetime

from .wordpress_entity import WPEntity, WPRequest, context_values
from .user import User
from .category import Category
from .media import Media

from .. import exc
from ..cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger("{}".format(__loader__.name.split(".")[0])) # package name

order_values = ["asc", "desc"]
orderby_values = ["author", "date", "id", "include", "modified", "parent",
				  "relevance", "slug", "title"]

class Post(WPEntity):

	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)
		self._schema_fields = None
		
		# related objects to cache
		self._author = None
		self._featured_media = None
		self._comments = None
		self._categories = None
			
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
			   "slug", "status", "type", "password", "title", "content", "author",
			   "excerpt", "featured_media", "comment_status", "ping_status", "format",
			   "meta", "sticky", "template", "categories", "tags"]
		return self._schema_fields

	@property
	def featured_media(self):
		'''
		Returns the 'Media' object that is the "featured media" for this post.
		'''
		if self._featured_media is None:
			
			media_id = self.s.featured_media
			if media_id == 0:
				# no featured media for this post entry (this is what WordPress returns)
				self._featured_media = None
			else:
				self._featured_media = self.api.media(id=media_id)
		return self._featured_media
	
	@featured_media.setter
	def featured_media(self, new_media):
		'''
		Set the "featured media" object to this post.
		'''
		if isinstance(new_media, Media) or new_media is None:
			self._featured_media = new_media
		else:
			raise ValueError("The featured media of a Post must be an object of class 'Media' ('{0}' provided).".format(type(new_media).__name__))
	
	@property
	def author(self):
		'''
		Returns the author of this post, class: 'User'.
		'''
		if self._author is None:
			try:
				self._author = self.api.user(id=self.s.author)  # ID for the author of the object
			except exc.NoEntityFound:
 				raise exc.UserNotFound("User ID '{0}' not found.".format(self.author))
# 			ur = self.api.UserRequest()
# 			ur.id = self.s.author # ID for the author of the object
# 			user_list = ur.get()
# 			if len(user_list) == 1:
# 				self._author = user_list[0]
# 			else:
# 				raise exc.UserNotFound("User ID '{0}' not found.".format(self.author))
		return self._author
	
	@author.setter
	def author(self, author):
		'''
		Set the related author object (class User).
		'''
		if isinstance(author, User) or author is None:
			self._author = author
		else:
			raise ValueError("The author of a Post must be an object of class 'User' ('{0}' provided).".format(type(new_media).__name__))

	
	@property
	def comments(self):
		'''
		Returns the comments associated with this post.
		'''
		if self._comments is None:
			self._comments = self.api.CommentRequest(post=self).get()
		return self._comments
	
	@property
	def categories(self):
		'''
		Returns a list of categories (as Category objects) associated with this post.
		'''
		if self._categories is None:
			self._categories = list()
			for category_id in self.s.categories:
				try:
					self._categories.append(self.api.category(id=category_id))
				except exc.NoEntityFound:
					logger.debug("Expected to find category ID={0} from post (ID={1}), but no category found.".format(category_id, self.s.id))
		return self._categories
	
	@property
	def category_names(self):
		return [x.s.name for x in self.categories]
	

class PostRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress posts.
	'''		
	def __init__(self, api=None, categories=None, slugs=None):		
		super().__init__(api=api)
		self.id = None # WordPress ID
		
		# values read from the response header
		self.total = None
		self.total_pages = None
		
		# parameters that undergo validation, i.e. need custom setter
		self._after = None
		self._before = None
		self._offset = None
		self._order = None
		self._orderby = None
		self._page = None
		self._per_page = None
		self._sticky = False
		
		self._status = list()
		self._author_ids = list()
		self._author_exclude = list()
		self._includes = list()
		self._slugs = list()
		self._category_ids = list()
		self._categories_exclude_ids = list()
		self._tags = list() # list of IDs of tags
		self._tags_exclude = list() # list of IDs of tags
				
		if categories:
			self.categories = categories
		if slugs:
			self.slugs = slugs
		
	@property
	def parameter_names(self):
		'''
		Post request parameters.
		'''
		return ["context", "page", "per_page", "search", "after", "author",
				"author_exclude", "before", "exclude", "include", "offset",
				"order", "orderby", "slug", "status", "categories",
				"categories_exclude", "tags", "tags_exclude", "sticky"]

	def get(self, count=False, embed=True):
		'''
		Returns a list of 'Post' objects that match the parameters set in this object.
		
		count : Boolean, if True, only returns the number of objects found.
		embed : include full content of linked resources in the response instead of just the ID, see: https://developer.wordpress.org/rest-api/using-the-rest-api/linking-and-embedding/#embedding
		'''
		self.url = self.api.base_url + "posts"
		
		if self.id:
			self.url += "/{}".format(self.id)

		# -------------------
		# populate parameters
		# -------------------
		if embed is True:
			self.parameters["_embed"] = "true"

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
			
		if self.after:
			self.parameters["after"] = self._after.isoformat()

		if len(self.author) > 0:
			# takes a list of author IDs
			self.parameters["author"] = ",".join(self.author)
		
		# author_exclude : Ensure result set excludes posts assigned to specific authors.
		if len(self.author_exclude) > 0:
			self.parameters["author_exclude"] = ",".join(self.author_exclude)
			
		# before : Limit response to posts published before a given ISO8601 compliant date.
		# TODO
		
		# exclude : Ensure result set excludes specific IDs.
		# TODO
		
		# include : Limit result set to specific IDs.
		if len(self.include) > 0:
			self.parameters["include"] = ",".join(self.include)
		
		# offset : Offset the result set by a specific number of items.
		if self.offset:
			self.parameters["offset"] = self.offset

		# order : Order sort attribute ascending or descending. Default: desc, one of: asc, desc
		if self.order:
			self.parameters["order"] = self.order

		# orderby : Sort collection by object attribute, default "date"
		# one of: author, date, id, include, modified, parent, relevance, slug, title
		if self.orderby:
			self.parameters["orderby"] = self.orderby

		# slug : Limit result set to posts with one or more specific slugs.
		if self.slug:
			self.parameters["slug"] = self.slug
			
		# status : Limit result set to posts assigned one or more statuses. (default: publish)
		if len(self.status) > 0:
			self.parameters["status"] = ",".join(self.status)

		# categories : Limit result set to all items that have the specified term assigned in the categories taxonomy.
		if len(self.categories) > 0:
			self.parameters["categories"] = ",".join(self.categories)

		# categories_exclude : Limit result set to all items except those that have the specified term assigned in the categories taxonomy.
		if len(self.categories_exclude) > 0:
			self.parameters["categories_exclude"] = ",".join(self.categories_exclude)

		# tags : Limit result set to all items that have the specified term assigned in the tags taxonomy. 
		if len(self.tags) > 0:
			self.parameters["tags"] = ",".join(self.tags)

		# tags_exclude : Limit result set to all items except those that have the specified term assigned in the tags taxonomy.
		if len(self.tags_exclude) > 0:
			self.parameters["tags_exclude"] = ",".join(self.tags_exclude)
					
		# sticky : Limit result set to items that are sticky.
		if self.sticky:
			self.parameters["sticky"] = "1"
		
		# -------------------

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
			
			raise Exception("Unhandled HTTP response, code {0}. Error: \n{1}\n".format(self.response.status_code, self.response.json()))

		
		# read response headers
		self.total = self.response.headers['X-WP-Total']
		self.total_pages = self.response.headers['X-WP-TotalPages']

		posts_data = self.response.json()

		if isinstance(posts_data, dict):
			# only one object was returned; make it a list
			posts_data = [posts_data]
	
		if count:
			return len(posts_data)
	
		posts = list()
		for d in posts_data:
		
			# Before we continue, do we have this Post in the cache already?
			try:
				post = self.api.wordpress_object_cache.get(class_name=Post.__name__, key=d["id"])
				posts.append(post)
				continue
			except WPORMCacheObjectNotFoundError:
				pass
			
			post = Post(api=self.api)
			post.json = json.dumps(d)

			post.update_schema_from_dictionary(d)

# 			# Properties applicable to 'view', 'edit', 'embed' query contexts
# 			#
# 			post.s.date = d["date"]
# 			post.s.id = d["id"]
# 			post.s.link = d["link"]
# 			post.s.slug = d["slug"]
# 			post.s.type = d["type"]
# 			post.s.author = d["author"]
# 			post.s.excerpt = d["excerpt"]["rendered"]
# 			post.s.featured_media = d["featured_media"]
# 			
# 			# Properties applicable to only 'view', 'edit' query contexts:
# 			#
# 			if request_context in ["view", "edit"]:
# 				post.s.date_gmt = d["date_gmt"]
# 				post.s.guid = d["guid"]
# 				post.s.modified = d["modified"]
# 				post.s.modified_gmt = d["modified_gmt"]
# 				post.s.status = d["status"]
# 				post.s.content = d["content"]["rendered"]
# 				post.s.comment_status = d["comment_status"]
# 				post.s.ping_status = d["ping_status"]
# 				post.s.format = d["format"]
# 				post.s.meta = d["meta"]
# 				post.s.sticky = d["sticky"]
# 				post.s.template = d["template"]
# 				post.s.categories = d["categories"]
# 				post.s.tags = d["tags"]
# 				
# 			# Properties applicable to only 'edit' query contexts
# 			#
# 			if request_context in ['edit']:
# 				post.s.password = d["password"]
# 			
# 			# Properties applicable to only 'view' query contexts
# 			#
# 			if request_context == 'view':
# 				post.s.title = d["title"]["rendered"]
# 			else:
# 				# not sure what the returned 'title' object looks like
# 				logger.debug(d)
# 				logger.debug(d["title"])
# 				logger.debug(request_context)
# 				raise NotImplementedError
		
			# Check for embedded content
			if "_embedded" in d:
				embedded = d["_embedded"]
				for key in embedded:
				
					# These are related objects, provided by the API in full.
					# See if the objects are in the cache first, and if not, create them.
				
					if key == "author":
						# value is a list of objects (dictionaries), only expecting one
						author_obj = embedded[key][0]
						try:
							author = self.api.wordpress_object_cache.get(class_name=User.__name__, key=author_obj["id"])
						except WPORMCacheObjectNotFoundError:
							author = User(api=self.api)
							author.update_schema_from_dictionary(author_obj)
							self.api.wordpress_object_cache.set(value=author, keys=(author.s.id, author.s.slug))
						
						post.author = author

					elif key == "wp:featuredmedia":
						# value is a list of objects (dictionaries), only expecting one
						media_obj = embedded[key][0]
						try:
							media = self.api.wordpress_object_cache.get(class_name=Media.__name__, key=media_obj["id"])
						except WPORMCacheObjectNotFoundError:
							media = Media(api=self.api)
							media.update_schema_from_dictionary(media_obj)
							self.api.wordpress_object_cache.set(value=media, keys=(media.s.id, media.s.slug))
							
						post.featured_media = media
					
					elif key == "wp:term":
						# value is list of lists,
						# first list is a list of metadata objects (can potentially be different kinds, or is this strictly 'category'?)
						# (this is not documented)
						# see: https://www.sitepoint.com/wordpress-term-meta/
						
						for term_list in embedded[key]:
							if len(term_list) == 0:
								continue
							for category_obj in term_list:
								if "taxonomy" in category_obj and category_obj["taxonomy"] in ["category", "post_tag", "nav_menu", "link_category", "post_format"]:
									try:
										category = self.api.wordpress_object_cache.get(class_name=Category.__name__,
																					   key=category_obj["id"])
									except WPORMCacheObjectNotFoundError:
										category = Category(api=self.api)
										category.update_schema_from_dictionary(category_obj)
										self.api.wordpress_object_cache.set(value=category, keys=(category.s.id, category.s.slug))
									
									post.categories.append(category)
									
								else:
									logger.warning("Unknown taxonomy encountered in _embedded data of Post (or something else entirely): {0}".format(json.dumps(term_list)))
					else:
						logger.debug("Note: Unhandled embedded content in {0}, key='{1}'".format(self.__class__.__name__, key))
					
			# add to cache
			self.api.wordpress_object_cache.set(value=post, keys=(post.s.id, post.s.slug))
			#self.api.wordpress_object_cache.set(class_name=Post.__name__, key=post.s.id, value=post)
			#self.api.wordpress_object_cache.set(class_name=Post.__name__, key=post.s.slug, value=post)
			
			posts.append(post)
			
		return posts
	
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
	def author(self):
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
	def author_exclude(self):
		return self._author_exclude
		
	@author_exclude.setter
	def author_exclude(self, value):
		'''
		Set author to exclude from this query; stores WordPress user ID.
		'''
		author_id = None
		
		# plan: define author_id, append to "self._author_ids" list below
		
		if value is None:
			self.parameters.pop("author_exclude", None) # remove key
			return
			#self.g = None

		elif isinstance(value, User):
			# a single user was given, replace any existing list with this one
			self._author_exclude = list()
			author_id = value.s.id

		elif isinstance(value, int):
			# a single id was given, replace any existing list with this one
			self._author_exclude = list()
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
					raise ValueError("Could not determine a user from the value: '{0}' (type '{1}')".format(value, type(value)))
							
		else:
			raise ValueError("Unexpected value type passed to 'author_exclude' (type: '{1}')".format(type(value)))
		
		assert author_id is not None, "Could not determine author_id from value '{0}'.".format(value)
		self._author_exclude.append(author_id)

	@property
	def after(self):
		'''
		WordPress parameter to return posts after this date.
		'''
		return self._after
	
	@after.setter
	def after(self, value):
		'''
		Set the WordPress parameter to return posts after this date.
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
		WordPress parameter to return posts before this date.
		'''
		return self._after
	
	@after.setter
	def before(self, value):
		'''
		Set the WordPress parameter to return posts before this date.
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
		return self._orderby # parameters.get('orderby', None)
		
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
		The list of post slugs to retrieve.
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

	@property
	def status(self):
		return self._status
	
	@status.setter
	def status(self, value):
		'''
		
		Note that 'status' may contain one or more values.
		Ref: https://developer.wordpress.org/rest-api/reference/posts/#arguments
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
	def categories(self):
		return self._category_ids

	@categories.setter
	def categories(self, values):
		'''
		This method validates the categories passed to this request.
		
		It accepts category ID (integer or string) or the slug value.
		'''
		if values is None:
			self.parameters.pop("categories", None)
			self._category_ids = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Categories must be provided as a list (or append to the existing list, or None).")
		
		for c in values:
			cat_id = None
			if isinstance(c, Category):
				cat_id = c.s.id
#				self._category_ids.append(str(c.s.id))
			elif isinstance(c, int):
#				self._category_ids.append(str(c))
				cat_id = c
			elif isinstance(c, str):
				try:
					# is this a category ID value?
					cat_id = int(c)
					#self._category_ids.append(str(int(c)))
				except ValueError:
					# not a category ID value, try by slug?
					try:
						category = self.api.category(slug=c)
						cat_id = category.s.id
						#self._category_ids.append(category.s.id)
					except exc.NoEntityFound:
						logger.debug("Asked to find a category with the slug '{0}' but not found.".format(slug))
			
			# Categories are stored as string ID values.
			#
			self._category_ids.append(str(cat_id))

	@property
	def categories_exclude(self):
		return self._category_exclude_ids

	@categories_exclude.setter
	def categories_exclude(self, values):
		'''
		This method validates the categories_exclude passed to this request.
		
		It accepts category ID (integer or string) or the slug value.
		'''
		if values is None:
			self.parameters.pop("categories_exclude", None)
			self._category_exclude_ids = list()
			return
		elif not isinstance(values, list):
			raise ValueError("categories_exclude must be provided as a list (or append to the existing list, or None).")
		
		for c in values:
			cat_id = None
			if isinstance(c, Category):
				cat_id = c.s.id
#				self._category_exclude_ids.append(str(c.s.id))
			elif isinstance(c, int):
#				self._category_exclude_ids.append(str(c))
				cat_id = c
			elif isinstance(c, str):
				try:
					# is this a category ID value?
					cat_id = int(c)
					#self._category_exclude_ids.append(str(int(c)))
				except ValueError:
					# not a category ID value, try by slug?
					try:
						category = self.api.category(slug=c)
						cat_id = category.s.id
						#self._category_exclude_ids.append(category.s.id)
					except exc.NoEntityFound:
						logger.debug("Asked to find a category with the slug '{0}' but not found.".format(slug))
			
			# Categories are stored as string ID values.
			#
			self._category_exclude_ids.append(str(cat_id))

	@property
	def tags(self):
		'''
		Return only items that have these tags.
		'''
		return self._tags
		
	@tags.setter
	def tags(self, values):
		'''
		List of tag IDs that are required to be attached to items returned from query.
		'''
		if values is None:
			self.parameters.pop("tags", None)
			self._tags = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Tags must be provided as a list of IDs (or append to the existing list).")
		
		for tag_id in values:
			if isinstance(tag_id, int):
				self.tags.append(tag_id)
			elif isinstance(tag_id, str):
				try:
					self.tags.append(str(int(tag_id)))
				except ValueError:
					raise ValueError("The given tag was in the form of a string but could not be converted to an integer ('{0}').".format(tag_id))
			else:
				raise ValueError("Unexpected type for property list 'tags'; expected str or int, got '{0}'".format(type(s)))			

	@property
	def tags_exclude(self):
		'''
		Return only items that do not have these tags.
		'''
		return self._tags_exclude
		
	@tags.setter
	def tags_exclude(self, values):
		'''
		List of tag IDs attached to items to be excluded from query.
		'''
		if values is None:
			self.parameters.pop("tags", None)
			self._tags_exclude = list()
			return
		elif not isinstance(values, list):
			raise ValueError("Tags must be provided as a list of IDs (or append to the existing list).")
		
		for tag_id in values:
			if isinstance(tag_id, int):
				self._tags_exclude.append(tag_id)
			elif isinstance(tag_id, str):
				try:
					self._tags_exclude.append(str(int(tag_id)))
				except ValueError:
					raise ValueError("The given tag was in the form of a string but could not be converted to an integer ('{0}').".format(tag_id))
			else:
				raise ValueError("Unexpected type for property list 'tags'; expected str or int, got '{0}'".format(type(s)))

	@property
	def sticky(self):
		'''
		If 'True', limits result set to items that are sticky.
		'''
		return self._sticky
		
	@sticky.setter
	def sticky(self, value):
		'''
		Set to 'True' to limit result set to items that are sticky.
		'''
		self._sticky = (value == True)



