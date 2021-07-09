import os
from urllib.parse import urljoin
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File
from pkg_resources import iter_entry_points

from .mkdocs_utils import docs_version_var

try:
    from mkdocs.exceptions import PluginError
except ImportError:  # pragma: no cover
    PluginError = ValueError


def get_theme_dir(theme_name):
    themes = list(iter_entry_points('mike.themes', theme_name))
    if len(themes) == 0:
        raise ValueError("theme '{}' unsupported".format(theme_name))
    return os.path.dirname(themes[0].load().__file__)


class MikePlugin(BasePlugin):
    config_scheme = (
        ('version_selector', config_options.Type(bool, default=True)),
        ('canonical_version',
         config_options.Type((str, type(None)), default=None)),
        ('css_dir', config_options.Type(str, default='css')),
        ('javascript_dir', config_options.Type(str, default='js')),
    )

    def on_config(self, config):
        version = os.environ.get(docs_version_var)
        if version and config.get('site_url'):
            if self.config['canonical_version'] is not None:
                version = self.config['canonical_version']
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

            extra_kind = 'extra_' + prop
            norm_extras = [os.path.normpath(i) for i in config[extra_kind]]
            for f in os.listdir(srcdir):
                relative_dest = os.path.join(cfg_value, f)
                if relative_dest in norm_extras:
                    raise PluginError('{!r} is already included in {!r}'
                                      .format(relative_dest, extra_kind))

                files.append(File(f, srcdir, destdir, False))
                config[extra_kind].append(relative_dest)
        return files
