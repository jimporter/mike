import os
import unittest
from collections import namedtuple
from unittest import mock

from .. import *
from mike import mkdocs_plugin
from mike.mkdocs_utils import docs_version_var


class TestGetThemeDir(unittest.TestCase):
    def test_mkdocs_theme(self):
        theme_dir = mkdocs_plugin.get_theme_dir('mkdocs')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_bootswatch_theme(self):
        theme_dir = mkdocs_plugin.get_theme_dir('yeti')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_unknown_theme(self):
        self.assertRaises(ValueError, mkdocs_plugin.get_theme_dir, 'nonexist')


class PluginTest(unittest.TestCase):
    def make_plugin(self, **kwargs):
        p = mkdocs_plugin.MikePlugin()
        p.config = {k: v.default for k, v in p.config_scheme}
        p.config.update(kwargs)
        return p


class TestMkdocsPluginOnConfig(PluginTest):
    def test_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            config = {'site_url': 'https://example.com/'}
            self.make_plugin().on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/1.0')

    def test_no_site_url(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            config = {'site_url': ''}
            self.make_plugin().on_config(config)
            self.assertEqual(config['site_url'], '')

    def test_explicit_canonical(self):
        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            config = {'site_url': 'https://example.com/'}
            self.make_plugin(canonical_version='latest').on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/latest')

        with mock.patch('os.environ', {docs_version_var: '1.0'}):
            config = {'site_url': 'https://example.com/'}
            self.make_plugin(canonical_version='').on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/')

    def test_no_version(self):
        with mock.patch('os.environ', {}):
            config = {'site_url': 'https://example.com/'}
            self.make_plugin().on_config(config)
            self.assertEqual(config['site_url'], 'https://example.com/')


class TestMkdocsPluginOnFiles(PluginTest):
    MockTheme = namedtuple('MockTheme', ['name'])

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
        files = self.make_plugin(version_selector=False).on_files([], cfg)
        self.assertEqual(files, [])
