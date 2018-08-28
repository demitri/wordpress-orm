'''
WordPress API reference: https://developer.wordpress.org/rest-api/reference/post-statuses/
'''

import json
import logging
import requests

from .wordpress_entity import WPEntity, WPRequest

from .. import exc

logger = logging.getLogger("{}".format(__loader__.name.split(".")[0])) # package name

class PostStatus(WPEntity):
		
	def __init__(self, id=None, session=None, api=None):
		super().__init__(api=api)
		
	def __repr__(self):
		if len(self.s.name) < 11:
			truncated_name = self.s.name
		else:
			truncated_name = self.s.name[0:10] + "..."
		return "<WP {0} object at {1}, id={2}, title='{3}'>".format(self.__class__.__name__,
													 hex(id(self)), self.s.id, truncated_name)

	@property
	def schema_fields(self):
		return ["name", "private", "protected", "public", "queryable", "show_in_list", "slug"]

class PostStatusRequest(WPRequest):
	'''
	A class that encapsulates requests for WordPress post statuses.
	'''		
	def __init__(self, api=None, categories=None, slugs=None):		
		super().__init__(api=api)
		self.id = None # WordPress ID

		self.url = self.api.base_url + "statuses"
	
		# values read from the response header
		self.total = None
		self.total_pages = None
		
		# parameters that undergo validation, i.e. need custom setter
		pass
		
	@property
	def parameter_names(self):
		'''
		PostStatus request parameters.
		'''
		if self._parameter_names is None:
			self._parameter_names = ["context"]
		return self._parameter_names
	
	def populate_request_parameters(self):
		'''
		Populates 'self.parameters' to prepare for executing a request.
		'''
		if self.context:
			self.parameters["context"] = self.context
			request_context = self.context
		else:
			if count:
				request_context = "embed" # only counting results, this is a shorter response
			else:
				request_context = "view" # default value
	
	def get(self, class_object=PostStatus, count=False):
		'''
		Returns a list of 'PostStatus' objects that match the parameters set in this object.
		
		count : Boolean, if True, only returns the number of objects found.
		'''
		
		populate_request_parameters() # populates 'self.parameters'
		
		try:
			self.get_response()
			logger.debug("URL='{}'".format(self.request.url))
		except requests.exceptions.HTTPError:
			logger.debug("PostStatus response code: {}".format(self.response.status_code))
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
			# return len(posts_data)
			
		if isinstance(poststatus_data, dict):
			# only one object was returned; make it a list
			poststatus_data = [poststatus_data]
		
		post_statuses = list()
		for d in poststatus_data:
		
			# TODO: check cache? This is not an object that has an ID

			post_status = classobject.__new__(classobject) # default = PostStatus()
			post_status.__init__(api=self.api)
			post_status.json = json.dumps(d)
			
			# perform postprocessing for custom fields
			post_status.postprocess_response()
			
			raise NotImplementedError("Not yet finished.")

				