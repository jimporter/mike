import os
import unittest

from . import assertPopen
from .. import *


class TestInstallExtras(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('install_extras')
        self.mkdocs_yml = os.path.join(self.stage, 'mkdocs.yml')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)

    def _test_extras(self):
        assertDirectory('.', {
            'mkdocs.yml',
            'docs',
            'docs/css',
            'docs/css/version-select.css',
            'docs/js',
            'docs/js/version-select.js',
            'docs/index.md',
        })

    def test_default(self):
        assertPopen(['mike', 'install-extras'])
        self._test_extras()

    def test_explicit_theme(self):
        assertPopen(['mike', 'install-extras', '-t', 'mkdocs'])
        self._test_extras()
