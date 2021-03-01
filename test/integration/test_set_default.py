import os
import unittest

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils


class SetDefaultTestCase(unittest.TestCase):
    def _deploy(self, branch=None, versions=['1.0']):
        branch_args = ['-b', branch] if branch else []
        for i in versions:
            assertPopen(['mike', 'deploy', i] + branch_args)

    def _test_default(self, expr=r'window\.location\.replace\("1\.0"\)',
                      expected_message=None):
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(message,
                             r'^Set default version to \S+ with mike \S+$')

        with open('index.html') as f:
            self.assertRegex(f.read(), expr)


class TestSetDefault(SetDefaultTestCase):
    def setUp(self):
        self.stage = stage_dir('set_default')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_set_default(self):
        self._deploy()
        assertPopen(['mike', 'set-default', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_custom_template(self):
        self._deploy()
        assertPopen(['mike', 'set-default', '1.0', '-T',
                     os.path.join(test_data_dir, 'template.html')])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default(r'^Redirecting to 1\.0$')

    def test_from_subdir(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'set-default', '1.0'], returncode=1)
            assertPopen(['mike', 'set-default', '1.0', '-F', '../mkdocs.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_from_subdir_explicit_origin(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'set-default', '1.0', '-b', 'gh-pages',
                         '-r', 'origin'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'set-default', '1.0', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_default()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'set-default', '1.0', '-m', 'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default(expected_message='commit message')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'set-default', '1.0', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)

    def test_remote_empty(self):
        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._deploy()
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'set-default', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'set-default', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._deploy(versions=['2.0'])
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'set-default', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        self._deploy()

        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['mike', 'set-default', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        self._deploy()

        stage_dir('set_default_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')

        self._deploy(versions=['2.1'])
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'set-default', '1.0'], output=(
            'mike: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'set-default', '--ignore', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)

        assertPopen(['mike', 'set-default', '--rebase', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)


class TestSetDefaultOtherRemote(SetDefaultTestCase):
    def setUp(self):
        self.stage_origin = stage_dir('set_default_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

    def _clone(self):
        self.stage = stage_dir('set_default_remote_clone')
        check_call_silent(['git', 'clone', self.stage_origin, '.'])
        git_config()

    def _test_rev(self, branch):
        clone_rev = git_utils.get_latest_commit(branch)
        with pushd(self.stage_origin):
            self.assertEqual(git_utils.get_latest_commit(branch), clone_rev)

    def test_default(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'set-default', '1.0', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_default()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        self._deploy(branch='pages')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'set-default', '1.0', '-p', '-b', 'pages'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_default()
        self._test_rev('pages')

    def test_explicit_remote(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['mike', 'set-default', '1.0', '-p', '-r', 'remote'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_default()
        self._test_rev('mybranch')
