import os
import re
import unittest

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions


def match_redir(url):
    return r'window\.location\.replace\("{}"\)'.format(re.escape(url))


class AliasTestCase(unittest.TestCase):
    def _deploy(self, branch=None, versions=['1.0'], prefix=''):
        extra_args = ['-b', branch] if branch else []
        if prefix:
            extra_args.extend(['--prefix', prefix])
        for i in versions:
            assertPopen(['mike', 'deploy', i] + extra_args)

    def _test_alias(self, expected_message=None,
                    expected_versions=[versions.VersionInfo('1.0')],
                    redirect=True, directory='.'):
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(message,
                             r'^Copied \S+ to latest( in .*)? with mike \S+$')

        files = {'versions.json'}
        for v in expected_versions:
            v_str = str(v.version)
            files |= {v_str, v_str + '/index.html',
                      v_str + '/css/version-select.css',
                      v_str + '/js/version-select.js'}
            for a in v.aliases:
                files |= {a, a + '/index.html'}
                if not redirect:
                    files |= {a + '/css/version-select.css',
                              a + '/js/version-select.js'}
        assertDirectory(directory, files, allow_extra=True)

        with open(os.path.join(directory, 'versions.json')) as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', aliases=['latest']),
            ])


class TestAlias(AliasTestCase):
    def setUp(self):
        self.stage = stage_dir('alias')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_alias(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

        with open('latest/index.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/'))

    def test_alias_copy(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest', '--no-redirect'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(redirect=False)

    def test_aliases_custom_template(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest', '-T',
                     os.path.join(test_data_dir, 'template.html')])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

        with open('latest/index.html') as f:
            self.assertEqual(f.read(), 'Redirecting to ../1.0/')

    def test_from_subdir(self):
        self._deploy()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'alias', '1.0', 'latest'], returncode=1)
            assertPopen(['mike', 'alias', '1.0', 'latest', '-F',
                         '../mkdocs.yml'])
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

    def test_prefix(self):
        self._deploy(prefix='prefix')
        assertPopen(['mike', 'alias', '1.0', 'latest', '--prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(directory='prefix')

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


class TestAliasOtherRemote(AliasTestCase):
    def setUp(self):
        self.stage_origin = stage_dir('alias_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

    def _clone(self):
        self.stage = stage_dir('alias_remote_clone')
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

        assertPopen(['mike', 'alias', '1.0', 'latest', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_alias()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        self._deploy(branch='pages')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'alias', '1.0', 'latest', '-p', '-b', 'pages'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_alias()
        self._test_rev('pages')

    def test_explicit_remote(self):
        self._deploy()
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['mike', 'alias', '1.0', 'latest', '-p', '-r', 'remote'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_alias()
        self._test_rev('mybranch')


class TestAliasNoDirectoryUrls(AliasTestCase):
    def setUp(self):
        self.stage = stage_dir('alias_no_directory_urls')
        git_init()
        copytree(os.path.join(test_data_dir, 'no_directory_urls'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_default(self):
        self._deploy()
        assertPopen(['mike', 'alias', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])

        with open('latest/index.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/index.html'))
        with open('latest/page.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/page.html'))
