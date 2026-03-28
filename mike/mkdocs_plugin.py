import os
import sys
from urllib.parse import urljoin
from mkdocs.config import config_options as opts
from mkdocs.plugins import BasePlugin

from .mkdocs_utils import docs_version_var
from .commands import AliasType

if sys.version_info < (3, 10):
    import importlib_metadata as metadata
else:
    from importlib import metadata


def get_theme_dir(theme_name):
    try:
        theme = metadata.entry_points(group='mike.themes')[theme_name]
    except KeyError:
        raise ValueError('theme {!r} unsupported'.format(theme_name))
    return os.path.dirname(theme.load().__file__)


class MikePlugin(BasePlugin):
    config_scheme = (
        ('alias_type', opts.Choice(tuple(i.name for i in AliasType),
                                   default='symlink')),
        ('redirect_template', opts.Type((str, type(None)), default=None)),
        ('deploy_prefix', opts.Type(str, default='')),
        ('version_selector', opts.Type(bool, default=True)),
        ('canonical_version', opts.Type((str, type(None)), default=None)),
        ('css_dir', opts.Type(str, default='css')),
        ('javascript_dir', opts.Type(str, default='js')),
    )

    @classmethod
    def default(cls):
        plugin = cls()
        plugin.load_config({})
        plugin.on_config({})
        return plugin

    def on_config(self, config):
        version = os.environ.get(docs_version_var)
        if version and config.get('site_url'):
            if self.config['canonical_version'] is not None:
                version = self.config['canonical_version']
            config['site_url'] = urljoin(config['site_url'], version)

