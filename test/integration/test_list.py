from __future__ import unicode_literals

import subprocess
import unittest

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

        with git_utils.Commit('gh-pages', 'commit message') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json', all_versions.dumps()
            ))

    def _check_list(self, options=[], err_output=''):
        proc = subprocess.Popen(
            ['mike', 'list'] + options,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )

        stdout, stderr = proc.communicate()

        self.assertEqual(proc.returncode, 0)
        self.assertEqual(stdout,
                         '4.0 [dev, latest]\n' +
                         '3.0.3 (3.0) [stable]\n' +
                         '2.0.2 (2.0)\n' +
                         '1.0\n')
        self.assertEqual(stderr, err_output)

    def test_list(self):
        self._check_list()

    def test_local_empty(self):
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('list_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._check_list()
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), origin_rev)

    def test_ahead_remote(self):
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('list_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
        clone_rev = git_utils.get_latest_commit('gh-pages')

        self._check_list()
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_behind_remote(self):
        stage_dir('list_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            with git_utils.Commit('gh-pages', 'add file') as commit:
                commit.add_file(git_utils.FileInfo(
                    'file.txt', 'this is some text'
                ))
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        self._check_list()
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), origin_rev)

    def test_diverged_remote(self):
        stage_dir('list_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            with git_utils.Commit('gh-pages', 'add file') as commit:
                commit.add_file(git_utils.FileInfo(
                    'file-origin.txt', 'this is some text'
                ))
            origin_rev = git_utils.get_latest_commit('gh-pages')

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        self._check_list(err_output=(
            'warning: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ))
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        self._check_list(['--ignore'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        self._check_list(['--rebase'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), origin_rev)
