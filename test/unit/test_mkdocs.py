from __future__ import unicode_literals

import os
import unittest
from six import assertRegex

from .. import *
from mkultra import mkdocs


class TestMkDocs(unittest.TestCase):
    def test_build(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        mkdocs.build()

        self.assertTrue(os.path.exists('site/index.html'))

    def test_version(self):
        assertRegex(self, mkdocs.version(), r'\S+')
