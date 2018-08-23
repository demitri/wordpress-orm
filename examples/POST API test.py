#!/usr/bin/env python

import os
import sys
import logging
import coloredlogs
from requests.auth import HTTPBasicAuth

sys.path.append('/Users/demitri/Documents/Repositories/GitHub/wordpress_orm')

import wordpress_orm as wp
from wordpress_orm import wp_session, exc
from wordpress_orm.entities import Post

# coloredlogs is configured with environment variables... weird
# define them here instead of from the shell
os.environ["COLOREDLOGS_LOG_FORMAT"] = "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"

logger = logging.getLogger("wordpress_orm")
logger.setLevel(logging.DEBUG)

use_color_logs = True
if use_color_logs:
	coloredlogs.install(level=logging.DEBUG, logger=logger)
else:
	ch = logging.StreamHandler() # output to console
	ch.setLevel(logging.DEBUG)   # set log level for output
	logger.addHandler(ch)        # add to logger

wordpress_api = wp.API(url="http://brie6.cshl.edu/wordpress/index.php/wp-json/wp/v2/")
wordpress_api.authenticator = HTTPBasicAuth(os.environ['SB_WP_USERNAME'], os.environ['SB_WP_PASSWORD'])

with wordpress_api.Session():
	new_post = Post(api=wordpress_api)
	logger.debug(new_post)
	new_post.s.title = "API POST Test: New Post Title"
	new_post.s.slug = "api-post-test-new-post-title"
	new_post.s.content = "This is content for a new post."
	new_post.s.excerpt = "This is the new post's excerpt, which appears to be required."
	new_post.s.sticky = True
	new_post.post()

