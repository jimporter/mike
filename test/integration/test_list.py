import json
import os
import subprocess
import unittest

from . import assertPopen
from .. import *
from mike import git_utils, versions

_default_output = ('4.0 [dev, latest]\n' +
                   '"3.0.3" (3.0) [stable]\n' +
                   '"2.0.2" (2.0)\n' +
                   '1.0\n')


class ListTestCase(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('list')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

        all_versions = versions.Versions()
        all_versions.add('1.0')
        all_versions.add('2.0', '2.0.2')
        all_versions.add('3.0', '3.0.3', ['stable'])
        all_versions.add('4.0', aliases=['latest', 'dev'])

        with git_utils.Commit('gh-pages', 'commit message') as commit:
            commit.add_file(git_utils.FileInfo(
                os.path.join(self.prefix, 'versions.json'),
                all_versions.dumps()
            ))

    def _get_list(self, options=[]):
        extra_args = ['--prefix', self.prefix] if self.prefix else []
        return subprocess.run(
            ['mike', 'list'] + options + extra_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True
        )

    def _check_list(self, options=[], stdout=_default_output, stderr='',
                    returncode=0):
        proc = self._get_list(options)
        self.assertEqual(proc.returncode, returncode)
        self.assertEqual(proc.stdout, stdout)
        self.assertEqual(proc.stderr, stderr)


class TestList(ListTestCase):
    prefix = ''

    def test_list(self):
        self._check_list()

    def test_list_version(self):
        self._check_list(['1.0'], '1.0\n')
        self._check_list(['4.0'], '4.0 [dev, latest]\n')
        self._check_list(['stable'], '"3.0.3" (3.0) [stable]\n')
        self._check_list(['nonexist'], '',
                         'mike: version nonexist does not exist\n', 1)

    def test_list_json(self):
        proc = self._get_list(['-j'])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, '')

        data = json.loads(proc.stdout)
        data[0]['aliases'].sort()
        self.assertEqual(data, [
            {'version': '4.0', 'title': '4.0', 'aliases': ['dev', 'latest']},
            {'version': '3.0', 'title': '3.0.3', 'aliases': ['stable']},
            {'version': '2.0', 'title': '2.0.2', 'aliases': []},
            {'version': '1.0', 'title': '1.0', 'aliases': []}
        ])

    def test_list_version_json(self):
        proc = self._get_list(['-j', 'stable'])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, '')
        self.assertEqual(json.loads(proc.stdout), {
            'version': '3.0', 'title': '3.0.3', 'aliases': ['stable']
        })

    def test_from_subdir(self):
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'list', '1.0'], returncode=1)

            opts = ['-F', '../mkdocs.yml']
            self._check_list(['1.0'] + opts, '1.0\n')
            self._check_list(['4.0'] + opts, '4.0 [dev, latest]\n')
            self._check_list(['stable'] + opts, '"3.0.3" (3.0) [stable]\n')
            self._check_list(['nonexist'] + opts, '',
                             'mike: version nonexist does not exist\n', 1)

            self._check_list(['1.0', '-b', 'gh-pages', '-r', 'origin'],
                             '1.0\n')

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

        self._check_list(stderr=(
            'warning: gh-pages has diverged from origin/gh-pages\n' +
            '  Pass --ignore to ignore this or --rebase to rebase onto ' +
            'remote\n'
        ))
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        self._check_list(['--ignore'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        self._check_list(['--rebase'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), origin_rev)


class TestListPrefix(ListTestCase):
    prefix = 'prefix'

    def test_list(self):
        self._check_list()

    def test_list_version(self):
        self._check_list(['1.0'], '1.0\n')
        self._check_list(['4.0'], '4.0 [dev, latest]\n')
        self._check_list(['stable'], '"3.0.3" (3.0) [stable]\n')
        self._check_list(['nonexist'], '',
                         'mike: version nonexist does not exist\n', 1)
