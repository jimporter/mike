import os
import unittest

from .. import *
from mike import mkdocs_utils


class TestMkDocsUtils(unittest.TestCase):
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

    def test_version(self):
        self.assertRegex(mkdocs_utils.version(), r'\S+')
