import os
import unittest
import yaml
from io import StringIO
from unittest import mock

from .. import *
from mike import mkdocs_utils


class Stream(StringIO):
    def __init__(self, name, data=''):
        super().__init__(data)
        self.name = name

    def close(self):
        pass


def mock_open_files(files):
    def wrapper(filename, *args, **kwargs):
        name = os.path.basename(filename)
        return Stream(name, files[name])

    return wrapper


# This mostly just tests `load_config` from MkDocs, but we want to be sure it
# behaves as we want it.
class TestLoadConfig(unittest.TestCase):
    def test_default(self):
        os.chdir(os.path.join(test_data_dir, 'basic_theme'))
        cfg = mkdocs_utils.load_config()
        self.assertEqual(cfg['site_dir'], os.path.abspath('site'))
        self.assertEqual(cfg['remote_name'], 'origin')
        self.assertEqual(cfg['remote_branch'], 'gh-pages')
        self.assertEqual(cfg['use_directory_urls'], True)

    def test_abs_path(self):
        cfg = mkdocs_utils.load_config(
            os.path.join(test_data_dir, 'basic_theme', 'mkdocs.yml')
        )
        self.assertEqual(cfg['site_dir'],
                         os.path.join(test_data_dir, 'basic_theme', 'site'))
        self.assertEqual(cfg['remote_name'], 'origin')
        self.assertEqual(cfg['remote_branch'], 'gh-pages')
        self.assertEqual(cfg['use_directory_urls'], True)

    def test_custom_site_dir(self):
        os.chdir(os.path.join(test_data_dir, 'site_dir'))
        cfg = mkdocs_utils.load_config()
        self.assertEqual(cfg['site_dir'], os.path.abspath('built_docs'))
        self.assertEqual(cfg['remote_name'], 'origin')
        self.assertEqual(cfg['remote_branch'], 'gh-pages')
        self.assertEqual(cfg['use_directory_urls'], True)

    def test_remote(self):
        os.chdir(os.path.join(test_data_dir, 'remote'))
        cfg = mkdocs_utils.load_config()
        self.assertEqual(cfg['site_dir'], os.path.abspath('site'))
        self.assertEqual(cfg['remote_name'], 'myremote')
        self.assertEqual(cfg['remote_branch'], 'mybranch')
        self.assertEqual(cfg['use_directory_urls'], True)

    def test_no_directory_urls(self):
        os.chdir(os.path.join(test_data_dir, 'no_directory_urls'))
        cfg = mkdocs_utils.load_config()
        self.assertEqual(cfg['site_dir'], os.path.abspath('site'))
        self.assertEqual(cfg['remote_name'], 'origin')
        self.assertEqual(cfg['remote_branch'], 'gh-pages')
        self.assertEqual(cfg['use_directory_urls'], False)

    def test_nonexist(self):
        os.chdir(os.path.join(test_data_dir, 'basic_theme'))
        with self.assertRaisesRegex(FileNotFoundError, r"'nonexist.yml'"):
            mkdocs_utils.load_config('nonexist.yml')
        with self.assertRaisesRegex(FileNotFoundError, r"'nonexist.yml'"):
            mkdocs_utils.load_config(['nonexist.yml', 'nonexist2.yml'])

        cfg = mkdocs_utils.load_config(['nonexist.yml', 'mkdocs.yml'])
        self.assertEqual(cfg['site_dir'], os.path.abspath('site'))
        self.assertEqual(cfg['remote_name'], 'origin')
        self.assertEqual(cfg['remote_branch'], 'gh-pages')
        self.assertEqual(cfg['use_directory_urls'], True)


class TestInjectPlugin(unittest.TestCase):
    @staticmethod
    def mock_open(read_data):
        m = mock.mock_open(read_data=read_data)

        def wrapper(file, *args, **kwargs):
            result = m(file, *args, **kwargs)
            result.name = file
            return result

        return wrapper

    def test_no_plugins(self):
        out = Stream('mike-mkdocs.yml')
        cfg = '{}'
        with mock.patch('builtins.open', self.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, out.name)
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': ['mike', 'search']})

    def test_other_plugins(self):
        out = Stream('mike-mkdocs.yml')
        cfg = 'plugins:\n  - foo\n  - bar:\n      option: true'
        with mock.patch('builtins.open', self.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, out.name)
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': [
            'mike', 'foo', {'bar': {'option': True}},
        ]})

    def test_other_plugins_dict(self):
        out = Stream('mike-mkdocs.yml')
        cfg = 'plugins:\n  foo: {}\n  bar:\n    option: true'
        with mock.patch('builtins.open', self.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, out.name)
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': {
            'mike': {}, 'foo': {}, 'bar': {'option': True},
        }})
        self.assertEqual(
            list(newcfg['plugins'].items()),
            [('mike', {}), ('foo', {}), ('bar', {'option': True})]
        )

    def test_mike_plugin(self):
        out = Stream('mike-mkdocs.yml')
        cfg = 'plugins:\n  - mike'
        with mock.patch('builtins.open', self.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, 'mkdocs.yml')
                self.assertEqual(out.getvalue(), '')
            mremove.assert_not_called()

    def test_mike_plugin_options(self):
        out = Stream('mike-mkdocs.yml')
        cfg = 'plugins:\n  - mike:\n      option: true'
        with mock.patch('builtins.open', self.mock_open(read_data=cfg)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, 'mkdocs.yml')
                self.assertEqual(out.getvalue(), '')
            mremove.assert_not_called()

    def test_inherit(self):
        out = Stream('mike-mkdocs.yml')
        main_cfg = 'INHERIT: mkdocs-base.yml\nplugins:\n  foo: {}\n'
        base_cfg = 'plugins:\n  bar: {}\n'
        files = {'mkdocs.yml': main_cfg, 'mkdocs-base.yml': base_cfg}
        with mock.patch('builtins.open', mock_open_files(files)), \
             mock.patch('mike.mkdocs_utils.NamedTemporaryFile',
                        return_value=out), \
             mock.patch('os.path.exists', return_value=True), \
             mock.patch('os.remove') as mremove:
            with mkdocs_utils.inject_plugin('mkdocs.yml') as f:
                self.assertEqual(f, 'mike-mkdocs.yml')
                newcfg = yaml.load(out.getvalue(), Loader=yaml.Loader)
            mremove.assert_called_once()

        self.assertEqual(newcfg, {'plugins': {
            'mike': {}, 'bar': {}, 'foo': {},
        }})
        self.assertEqual(
            list(newcfg['plugins'].items()),
            [('mike', {}), ('bar', {}), ('foo', {})]
        )


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
