import os
import unittest

from .. import *
from mike import mkdocs


class TestMkDocs(unittest.TestCase):
    def test_build(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        mkdocs.build(verbose=False)

        self.assertTrue(os.path.exists('site/index.html'))

    def test_build_explicit_cfg(self):
        self.stage = stage_dir('build')
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)

        # XXX: It'd be nice if we could change directory here to ensure this
        # works, but mkdocs hasn't released a final version with the
        # paths-are-relative-to-config behavior yet...
        mkdocs.build(config_file=os.path.join(self.stage, 'mkdocs.yml'),
                     verbose=False)

        self.assertTrue(os.path.exists('site/index.html'))

    def test_version(self):
        self.assertRegex(mkdocs.version(), r'\S+')
