import os
import unittest
from collections import namedtuple
from unittest import mock

from .. import *
from mike.mkdocs_utils import docs_version_var


class MockPlugins:
    BasePlugin = object


# Mock importing `mkdocs.plugins`, since it can't be imported normally.
real_import = __import__
with mock.patch('builtins.__import__',
                lambda name, *args: (MockPlugins if name == 'mkdocs.plugins'
                                     else real_import(name, *args))):
    from mike import mkdocs_plugin


class TestGetThemeDir(unittest.TestCase):
    def test_mkdocs_theme(self):
        theme_dir = mkdocs_plugin.get_theme_dir('mkdocs')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_bootswatch_theme(self):
        theme_dir = mkdocs_plugin.get_theme_dir('yeti')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_unknown_theme(self):
        self.assertRaises(ValueError, mkdocs_plugin.get_theme_dir, 'nonexist')


class TestMkdocsPluginOnConfig(unittest.TestCase):
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


class TestMkdocsPluginOnFiles(unittest.TestCase):
    MockTheme = namedtuple('MockTheme', ['name'])

    def make_plugin(self, version_selector=True):
        p = mkdocs_plugin.MikePlugin()
        p.config = {'version_selector': version_selector, 'css_dir': 'css',
                    'javascript_dir': 'js'}
        return p

    def make_config(self, theme, extra_css=[], extra_javascript=[]):
        return {'theme': self.MockTheme(theme),
                'site_dir': os.path.abspath(test_data_dir),
                'extra_css': list(extra_css),
                'extra_javascript': list(extra_javascript)}

    def test_mkdocs_theme(self):
        cfg = self.make_config('mkdocs')
        files = self.make_plugin().on_files([], cfg)
        self.assertEqual([i.src_path for i in files],
                         ['version-select.css', 'version-select.js'])

    def test_unrecognized_theme(self):
        cfg = self.make_config('unrecognized')
        files = self.make_plugin().on_files([], cfg)
        self.assertEqual(files, [])

    def test_duplicate_files(self):
        cfg = self.make_config('mkdocs', ['css/version-select.css'])
        with self.assertRaises(mkdocs_plugin.PluginError):
            self.make_plugin().on_files([], cfg)

    def test_no_version_select(self):
        cfg = self.make_config('mkdocs')
        files = self.make_plugin(False).on_files([], cfg)
        self.assertEqual(files, [])
