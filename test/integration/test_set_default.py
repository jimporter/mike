from __future__ import unicode_literals

import os
import subprocess
import unittest
from six import assertRegex

from . import assertPopen
from .. import *
from mike import git_utils


class TestSetDefault(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('set_default')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _deploy(self, branch='gh-pages'):
        assertPopen(['mike', 'deploy', '-b', branch, '1.0'])

    def _test_default(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message,
                        r'^Set default version to \S+ with mike \S+$')

        with open('index.html') as f:
            assertRegex(self, f.read(),
                        r'window\.location\.replace\("1\.0"\)')

    def test_set_default(self):
        self._deploy()
        assertPopen(['mike', 'set-default', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'set-default', '-b', 'branch', '1.0'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_default()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'set-default', '-m', 'commit message', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default('commit message')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'set-default', '-p', '1.0'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)
