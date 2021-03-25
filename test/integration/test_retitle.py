import os
import unittest

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions


class RetitleTestCase(unittest.TestCase):
    def _deploy(self, branch=None, versions=['1.0'], prefix=''):
        extra_args = ['-b', branch] if branch else []
        if prefix:
            extra_args.extend(['--prefix', prefix])
        for i in versions:
            assertPopen(['mike', 'deploy', i] + extra_args)

    def _test_retitle(self, expected_message=None, directory='.'):
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Set title of \S+ to 1\.0\.1( in .*)? with mike \S+$'
            )

        assertDirectory(directory, {
            'versions.json',
            '1.0/index.html',
        }, allow_extra=True)

        with open(os.path.join(directory, 'versions.json')) as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', '1.0.1'),
            ])


class TestRetitle(RetitleTestCase):
    def setUp(self):
        self.stage = stage_dir('retitle')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_retitle(self):
        self._deploy()
        assertPopen(['mike', 'retitle', '1.0', '1.0.1'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle()

    def test_branch(self):
        self._deploy('branch')
        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_retitle()

    def test_from_subdir(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'retitle', '1.0', '1.0.1'], returncode=1)
            assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-F',
                         '../mkdocs.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle()

    def test_from_subdir_explicit_branch(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-b', 'gh-pages',
                         '-r', 'origin'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle()

    def test_commit_message(self):
        self._deploy()
        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-m',
                     'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle('commit message')

    def test_prefix(self):
        self._deploy(prefix='prefix')
        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '--prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle(directory='prefix')

    def test_push(self):
        self._deploy()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)

    def test_remote_empty(self):
        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._deploy()
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'retitle', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'retitle', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        self._deploy()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._deploy(versions=['2.0'])
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'retitle', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        self._deploy()

        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['mike', 'retitle', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        self._deploy()

        stage_dir('retitle_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._deploy(versions=['2.0'])
            origin_rev = git_utils.get_latest_commit('gh-pages')

        self._deploy(versions=['2.1'])
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'retitle', '1.0', '1.0.1'], output=(
            'error: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'retitle', '--ignore', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)

        assertPopen(['mike', 'retitle', '--rebase', '1.0', '1.0.1'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)


class TestRetitleOtherRemote(RetitleTestCase):
    def setUp(self):
        self.stage_origin = stage_dir('retitle_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

    def _clone(self):
        self.stage = stage_dir('retitle_remote_clone')
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

        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_retitle()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        self._deploy(branch='pages')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-p', '-b', 'pages'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_retitle()
        self._test_rev('pages')

    def test_explicit_remote(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['mike', 'retitle', '1.0', '1.0.1', '-p', '-r', 'remote'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_retitle()
        self._test_rev('mybranch')
