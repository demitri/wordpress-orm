
name = "wordpress_orm"

from .api import API
import logging
from .api import wp_session

from .entities.wordpress_entity import WPEntity, WPRequest
from .cache import WPORMCacheObjectNotFoundError

logger = logging.getLogger(__name__.split(".")[0]) # package name
