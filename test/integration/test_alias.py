from __future__ import unicode_literals

import os
import subprocess
import unittest
from six import assertRegex

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions


class TestAlias(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('alias')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _deploy(self, branch='gh-pages', versions=['1.0']):
        for i in versions:
            assertPopen(['mike', 'deploy', '-b', branch, i])

    def _test_alias(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message,
                        r'^Copied \S+ to latest with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '1.0/index.html',
            'latest/index.html',
        }, allow_extra=True)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', aliases=['latest']),
            ])

    def test_alias(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'alias', '1.0', 'latest', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_alias()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest', '-m',
                     'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias('commit message')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'alias', '1.0', 'latest', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)

    def test_remote_empty(self):
        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._deploy()
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'alias', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'alias', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._deploy(versions=['2.0'])
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'alias', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        self._deploy()

        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['mike', 'alias', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        self._deploy()

        stage_dir('alias_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')

        self._deploy(versions=['2.1'])
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'alias', '1.0', 'latest'], output=(
            'mike: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'alias', '--ignore', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)

        assertPopen(['mike', 'alias', '--rebase', '1.0', 'latest'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)
