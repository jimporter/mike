import os
import unittest
import yaml
from io import StringIO
from unittest import mock

from .. import *
from mike import mkdocs_utils


class TestSiteDir(unittest.TestCase):
    def test_site_dir(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        self.assertEqual(mkdocs_utils.site_dir('mkdocs.yml'), 'site')
        self.assertEqual(
            mkdocs_utils.site_dir(os.path.join(self.stage, 'mkdocs.yml')),
            os.path.join(self.stage, 'site')
        )

    def test_custom_site_dir(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'site_dir'), self.stage)
        self.assertEqual(mkdocs_utils.site_dir('mkdocs.yml'), 'built_docs')
        self.assertEqual(
            mkdocs_utils.site_dir(os.path.join(self.stage, 'mkdocs.yml')),
            os.path.join(self.stage, 'built_docs')
        )


class TestInjectPlugin(unittest.TestCase):
    class Stream(StringIO):
        name = 'mike-mkdocs.yml'

        def close(self):
            pass

    def test_no_plugins(self):
        out = self.Stream()
        cfg = '{}'
        with mock.patch('builtins.open', mock.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:  # noqa
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, out.name)
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': ['mike']})

    def test_other_plugins(self):
        out = self.Stream()
        cfg = 'plugins:\n  - foo\n  - bar:\n      option: true'
        with mock.patch('builtins.open', mock.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:  # noqa
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, out.name)
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': [
            'mike', 'foo', {'bar': {'option': True}}
        ]})

    def test_mike_plugin(self):
        out = self.Stream()
        cfg = 'plugins:\n  - mike'
        with mock.patch('builtins.open', mock.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:  # noqa
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, 'mkdocs.yml')
                self.assertEqual(out.getvalue(), '')
            mremove.assert_not_called()

    def test_mike_plugin_options(self):
        out = self.Stream()
        cfg = 'plugins:\n  - mike:\n      option: true'
        with mock.patch('builtins.open', mock.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:  # noqa
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, 'mkdocs.yml')
                self.assertEqual(out.getvalue(), '')
            mremove.assert_not_called()


class TestBuild(unittest.TestCase):
    def test_build(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        mkdocs_utils.build('mkdocs.yml', '1.0', verbose=False)

        self.assertTrue(os.path.exists('site/index.html'))

    def test_build_directory(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)

        # Change to a different directory to make sure that everything works,
        # including paths being relative to mkdocs.yml (which MkDocs itself is
        # responsible for).
        with pushd(this_dir):
            mkdocs_utils.build(os.path.join(self.stage, 'mkdocs.yml'),
                               '1.0', verbose=False)

        self.assertTrue(os.path.exists('site/index.html'))


class TestVersion(unittest.TestCase):
    def test_version(self):
        self.assertRegex(mkdocs_utils.version(), r'\S+')
