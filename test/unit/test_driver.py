import mkdocs.config
import os
import unittest
from argparse import Namespace
from unittest import mock

from .. import *
from mike import driver
from mike.commands import AliasType


class TestLoadMkdocsConfig(unittest.TestCase):
    def make_args(self, **kwargs):
        default = {'config_file': '/path/to/mkdocs.yml', 'branch': None,
                   'remote': None}
        default.update(kwargs)
        return Namespace(**default)

    def test_config(self):
        path = os.path.join(test_data_dir, 'basic_theme', 'mkdocs.yml')
        args = self.make_args(config_file=path)
        self.assertIsInstance(driver.load_mkdocs_config(args),
                              mkdocs.config.Config)
        self.assertFalse(hasattr(args, 'alias_type'))
        self.assertFalse(hasattr(args, 'template'))
        self.assertFalse(hasattr(args, 'deploy_prefix'))

        args = self.make_args(config_file=path, alias_type=None, template=None,
                              deploy_prefix=None)
        self.assertIsInstance(driver.load_mkdocs_config(args),
                              mkdocs.config.Config)
        self.assertEqual(args.alias_type, AliasType.redirect)
        self.assertEqual(args.template, None)
        self.assertEqual(args.deploy_prefix, '')

        args = self.make_args(config_file=path, alias_type=AliasType.copy,
                              template='file.html', deploy_prefix='prefix')
        self.assertIsInstance(driver.load_mkdocs_config(args),
                              mkdocs.config.Config)
        self.assertEqual(args.alias_type, AliasType.copy)
        self.assertEqual(args.template, 'file.html')
        self.assertEqual(args.deploy_prefix, 'prefix')

    def test_no_config(self):
        args = self.make_args(branch='gh-pages', remote='origin')
        with mock.patch('builtins.open', side_effect=FileNotFoundError):
            self.assertIs(driver.load_mkdocs_config(args), None)
            self.assertFalse(hasattr(args, 'alias_type'))
            self.assertFalse(hasattr(args, 'template'))
            self.assertFalse(hasattr(args, 'deploy_prefix'))

        args = self.make_args(branch='gh-pages', remote='origin',
                              alias_type=None, template=None,
                              deploy_prefix=None)
        with mock.patch('builtins.open', side_effect=FileNotFoundError):
            self.assertIs(driver.load_mkdocs_config(args), None)
            self.assertEqual(args.alias_type, AliasType.redirect)
            self.assertEqual(args.template, None)
            self.assertEqual(args.deploy_prefix, '')

        args = self.make_args(branch='gh-pages', remote='origin',
                              alias_type=AliasType.copy, template='file.html',
                              deploy_prefix='prefix')
        with mock.patch('builtins.open', side_effect=FileNotFoundError):
            self.assertIs(driver.load_mkdocs_config(args), None)
            self.assertEqual(args.alias_type, AliasType.copy)
            self.assertEqual(args.template, 'file.html')
            self.assertEqual(args.deploy_prefix, 'prefix')

    def test_no_config_missing_fields(self):
        args = self.make_args()
        with mock.patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                driver.load_mkdocs_config(args)
