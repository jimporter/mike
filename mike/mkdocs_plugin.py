import os
from urllib.parse import urljoin
from mkdocs.plugins import BasePlugin

from .mkdocs_utils import docs_version_var


class MikePlugin(BasePlugin):
    def on_config(self, config):
        version = os.environ.get(docs_version_var)
        if version and config.get('site_url'):
            config['site_url'] = urljoin(config['site_url'], version)
