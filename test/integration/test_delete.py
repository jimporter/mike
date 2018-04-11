from __future__ import unicode_literals

import os
import subprocess
import unittest
from six import assertRegex

from . import assertPopen
from .. import *
from mike import git_utils


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('delete')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _deploy(self, branch='gh-pages'):
        assertPopen(['mike', 'deploy', '-b', branch, '1.0'])
        assertPopen(['mike', 'deploy', '-b', branch, '2.0'])

    def _test_delete(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message, r'^Removed \S+ with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '2.0',
            '2.0/index.html'
        }, allow_extra=True)

    def test_delete_versions(self):
        self._deploy()
        assertPopen(['mike', 'delete', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_delete_all(self):
        self._deploy()
        assertPopen(['mike', 'delete', '--all'])
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        assertRegex(self, message, r'^Removed everything with mike \S+$')
        self.assertFalse(os.path.exists('version.json'))

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'delete', '-b', 'branch', '1.0'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_delete()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'delete', '-m', 'commit message', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete('commit message')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('delete_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'delete', '-p', '1.0'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)
