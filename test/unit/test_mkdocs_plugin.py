import unittest
from unittest import mock

from mike.mkdocs_utils import docs_version_var


class MockPlugins:
    BasePlugin = object


# Mock importing `mkdocs.plugins`, since it can't be imported normally.
real_import = __import__
with mock.patch('builtins.__import__',
                lambda name, *args: (MockPlugins if name == 'mkdocs.plugins'
                                     else real_import(name, *args))):
    from mike import mkdocs_plugin


class TestMkdocsPlugin(unittest.TestCase):
    def test_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = mkdocs_plugin.MikePlugin()
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/1.0')

    def test_no_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            p = mkdocs_plugin.MikePlugin()
            config = {'site_url': ''}
            p.on_config(config)
            self.assertEqual(config['site_url'], '')

    def test_no_version(self):
        with mock.patch('os.environ', {}):
            p = mkdocs_plugin.MikePlugin()
            config = {'site_url': 'https://example.com/'}
            p.on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/')
