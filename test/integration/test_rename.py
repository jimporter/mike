from __future__ import unicode_literals

import os
import subprocess
import unittest
from six import assertRegex

from . import assertPopen
from .. import *
from mike import git_utils, versions


class TestRename(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('rename')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _deploy(self, branch='gh-pages'):
        assertPopen(['mike', 'deploy', '-b', branch, '1.0'])

    def _test_rename(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message, r'^Set title of version \S+ to ' +
                        r'1\.0\.1 with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '1.0/index.html',
        }, allow_extra=True)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', '1.0.1'),
            ])

    def test_rename(self):
        self._deploy()
        assertPopen(['mike', 'rename', '1.0', '1.0.1'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_rename()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'rename', '1.0', '1.0.1', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_rename()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'rename', '1.0', '1.0.1', '-m',
                     'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_rename('commit message')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        clone = stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'rename', '1.0', '1.0.1', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)
