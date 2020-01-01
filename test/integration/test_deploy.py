import os
import subprocess
import unittest
from itertools import chain

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions


class TestDeploy(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('deploy')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _test_deploy(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('1.0')]):
        rev = git_utils.get_latest_commit('master', short=True)
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Deployed {} to {} with MkDocs \S+ and mike \S+$'
                .format(rev, expected_versions[0].version)
            )

        dirs = set()
        for i in expected_versions:
            dirs |= {str(i.version)} | i.aliases
        contents = {'versions.json'} | set(chain.from_iterable(
            (d, d + '/index.html') for d in dirs
        ))
        assertDirectory('.', contents, allow_extra=True)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())),
                             expected_versions)

    def test_default(self):
        assertPopen(['mike', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        assertPopen(['mike', 'deploy', '-t', '1.0.0', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.0')
        ])

    def test_aliases(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])

    def test_update(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        assertPopen(['mike', 'deploy', '-t', '1.0.1', '1.0', 'greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest', 'greatest'])
        ])

    def test_update_aliases(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        assertPopen(['mike', 'deploy', '-u', '2.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('2.0', aliases=['latest']),
            versions.VersionInfo('1.0'),
        ])

    def test_from_subdir(self):
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'deploy', '1.0', '-F', '../mkdocs.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_branch(self):
        assertPopen(['mike', 'deploy', '-b', 'branch', '1.0'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        assertPopen(['mike', 'deploy', '-m', 'commit message', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('commit message')

    def test_push(self):
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'deploy', '-p', '1.0'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            self.assertEqual(git_utils.get_latest_commit('gh-pages'),
                             clone_rev)

    def test_remote_empty(self):
        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'deploy', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'deploy', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file2.txt', 'this is some text'
            ))
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'deploy', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))

        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            with git_utils.Commit('gh-pages', 'add file') as commit:
                commit.add_file(git_utils.FileInfo(
                    'file2.txt', 'this is some text'
                ))
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['mike', 'deploy', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))

        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            with git_utils.Commit('gh-pages', 'add file') as commit:
                commit.add_file(git_utils.FileInfo(
                    'file2-origin.txt', 'this is some text'
                ))
            origin_rev = git_utils.get_latest_commit('gh-pages')

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file2.txt', 'this is some text'
            ))
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'deploy', '1.0'], output=(
            'mike: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'deploy', '--ignore', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)

        assertPopen(['mike', 'deploy', '--rebase', '1.0'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)
