from __future__ import unicode_literals

import os
import unittest

from . import assertPopen
from .. import *
from mike import git_utils, versions


class TestList(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('list')
        git_init()
        all_versions = versions.Versions()
        all_versions.add('1.0')
        all_versions.add('2.0', '2.0.2')
        all_versions.add('3.0', '3.0.3', ['stable'])
        all_versions.add('4.0', aliases=['latest', 'dev'])

        commit = git_utils.Commit('gh-pages', 'commit message')
        commit.add_file(git_utils.FileInfo(
            'versions.json', all_versions.dumps()
        ))
        commit.finish()

    def test_list(self):
        self.assertEqual(
            assertPopen(['mike', 'list']),
            '4.0 [dev, latest]\n' +
            '3.0.3 (3.0) [stable]\n' +
            '2.0.2 (2.0)\n' +
            '1.0\n'
        )
