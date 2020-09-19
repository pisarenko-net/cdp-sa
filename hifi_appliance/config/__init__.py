import sys
import yaml

from .cd import *
from .db import *
from .media import *
from ..constants import CONFIG_PATH_NAME


try:
	with open(CONFIG_PATH_NAME, 'r') as f:
		this_module = sys.modules[__name__]
		user_config = yaml.load(f, Loader=yaml.BaseLoader)
		for key in user_config.keys():
			setattr(this_module, key, user_config[key])
except Exception:
	pass
