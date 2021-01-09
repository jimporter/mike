import os
from urllib.parse import urljoin
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File
from pkg_resources import iter_entry_points

from .mkdocs_utils import docs_version_var


def get_theme_dir(theme_name):
    themes = list(iter_entry_points('mike.themes', theme_name))
    if len(themes) == 0:
        raise ValueError("theme '{}' unsupported".format(theme_name))
    return os.path.dirname(themes[0].load().__file__)


class MikePlugin(BasePlugin):
    config_scheme = (
        ('version_selector', config_options.Type(bool, default=True)),
        ('css_dir', config_options.Type(str, default='css')),
        ('javascript_dir', config_options.Type(str, default='js')),
    )

    def on_config(self, config):
        version = os.environ.get(docs_version_var)
        if version and config.get('site_url'):
            config['site_url'] = urljoin(config['site_url'], version)

    def on_files(self, files, config):
        if not self.config['version_selector']:
            return files

        try:
            theme_dir = get_theme_dir(config['theme'].name)
        except ValueError:
            return files

        for path, prop in [('css', 'css'), ('js', 'javascript')]:
            cfg_value = self.config[prop + '_dir']
            srcdir = os.path.join(theme_dir, path)
            destdir = os.path.join(config['site_dir'], cfg_value)

            extra_files = os.listdir(srcdir)
            for f in extra_files:
                files.append(File(f, srcdir, destdir, False))
                config['extra_' + prop].append(os.path.join(cfg_value, f))
        return files
