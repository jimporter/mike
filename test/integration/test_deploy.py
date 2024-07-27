import os
import sys
import unittest

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions
from mike.commands import AliasType


class DeployTestCase(unittest.TestCase):
    def _test_deploy(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('1.0')],
                     alias_type=AliasType.symlink, directory='.'):
        rev = git_utils.get_latest_commit('master', short=True)
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Deployed {} to {}( in .*)? with MkDocs \S+ and mike \S+$'
                .format(rev, expected_versions[0].version)
            )

        files = {'versions.json'}
        for v in expected_versions:
            v_str = str(v.version)
            files |= {v_str, v_str + '/index.html',
                      v_str + '/css/version-select.css',
                      v_str + '/js/version-select.js'}
            for a in v.aliases:
                files.add(a)
                if alias_type != AliasType.symlink:
                    files |= {a + '/index.html'}
                if alias_type == AliasType.copy:
                    files |= {a + '/css/version-select.css',
                              a + '/js/version-select.js'}
        assertDirectory(directory, files, allow_extra=True)

        with open(os.path.join(directory, 'versions.json')) as f:
            self.assertEqual(list(versions.Versions.loads(f.read())),
                             expected_versions)


class TestDeploy(DeployTestCase):
    def setUp(self):
        self.stage = stage_dir('deploy')
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_default(self):
        assertPopen(['mike', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        assertPopen(['mike', 'deploy', '1.0', '-t', '1.0.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.0')
        ])

    @unittest.skipIf(sys.platform == 'win32' and sys.version_info < (3, 8),
                     'this version of realpath fails to resolve symlinks')
    def test_aliases(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])
        self.assertTrue(os.path.islink('latest'))
        self.assertEqual(os.path.normcase(os.path.realpath('latest')),
                         os.path.normcase(os.path.abspath('1.0')))

    def test_aliases_redirect(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest',
                     '--alias-type=redirect'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ], alias_type=AliasType.redirect)
        with open('latest/index.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/'))

    def test_aliases_custom_redirect(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest',
                     '--alias-type=redirect', '-T',
                     os.path.join(test_data_dir, 'template.html')])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ], alias_type=AliasType.redirect)
        check_call_silent(['git', 'checkout', 'gh-pages'])

        with open('latest/index.html') as f:
            self.assertEqual(f.read(), 'Redirecting to ../1.0/\n')

    def test_aliases_copy(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest', '--alias-type=copy'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ], alias_type=AliasType.copy)

    def test_props(self):
        assertPopen(['mike', 'deploy', '1.0',
                     '--prop-set', 'foo.bar=[1,2,3]',
                     '--prop-set', 'foo.bar[1]=true',
                     '--prop-delete', 'foo.bar[0]'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', properties={'foo': {'bar': [True, 3]}})
        ])

    def test_update(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        assertPopen(['mike', 'deploy', '1.0', 'greatest', '-t', '1.0.1'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest', 'greatest'])
        ])

    def test_update_aliases(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest'])
        assertPopen(['mike', 'deploy', '2.0', 'latest', '-u'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('2.0', aliases=['latest']),
            versions.VersionInfo('1.0'),
        ])

    def test_update_aliases_with_version(self):
        assertPopen(['mike', 'deploy', '1.0b1', '1.0'])
        assertPopen(['mike', 'deploy', '1.0', 'latest', '-u'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest']),
            versions.VersionInfo('1.0b1'),
        ])

    def test_from_subdir(self):
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'deploy', '1.0'], returncode=1)
            assertPopen(['mike', 'deploy', '1.0', '-F', '../mkdocs.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_branch(self):
        assertPopen(['mike', 'deploy', '1.0', '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        assertPopen(['mike', 'deploy', '1.0', '-m', 'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('commit message')

    def test_deploy_prefix(self):
        assertPopen(['mike', 'deploy', '1.0', '--deploy-prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(directory='prefix')

    def test_double_deploy_prefix(self):
        assertPopen(['mike', 'deploy', '1.0'])
        assertPopen(['mike', 'deploy', '1.0', '--deploy-prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()
        self._test_deploy(directory='prefix')

    def test_push(self):
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'deploy', '1.0', '-p'])
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

        with pushd(self.stage), \
             git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file2-origin.txt', 'this is some text'
            ))

        with git_utils.Commit('gh-pages', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file2.txt', 'this is some text'
            ))
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'deploy', '1.0'], stdout='', stderr=(
            'error: gh-pages has diverged from origin/gh-pages\n' +
            "  If you're sure this is intended, retry with " +
            '--ignore-remote-status\n'
        ), returncode=1)
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'deploy', '1.0', '--ignore-remote-status'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)


class TestDeployMkdocsYaml(DeployTestCase):
    def setUp(self):
        self.stage = stage_dir('deploy_mkdocs_yaml')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs_yaml'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yaml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_default(self):
        assertPopen(['mike', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()


class TestDeployPlugin(DeployTestCase):
    def setUp(self):
        self.stage = stage_dir('deploy_plugin')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs_plugin'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_default(self):
        assertPopen(['mike', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(directory='prefix')


class TestDeployCustomSiteDir(DeployTestCase):
    def setUp(self):
        self.stage = stage_dir('deploy_sitedir')
        git_init()
        copytree(os.path.join(test_data_dir, 'site_dir'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_default(self):
        assertPopen(['mike', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()


class TestDeployOtherRemote(DeployTestCase):
    def setUp(self):
        self.stage_origin = stage_dir('deploy_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

        self.stage = stage_dir('deploy_remote_clone')
        check_call_silent(['git', 'clone', self.stage_origin, '.'])
        git_config()

    def _test_rev(self, branch):
        clone_rev = git_utils.get_latest_commit(branch)
        with pushd(self.stage_origin):
            self.assertEqual(git_utils.get_latest_commit(branch), clone_rev)

    def test_default(self):
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'deploy', '1.0', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_deploy()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'deploy', '1.0', '-b', 'pages', '-p'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_deploy()
        self._test_rev('pages')

    def test_explicit_remote(self):
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['mike', 'deploy', '1.0', '-r', 'remote', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_deploy()
        self._test_rev('mybranch')


class TestDeployNoDirectoryUrls(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('deploy_no_directory_urls')
        git_init()
        copytree(os.path.join(test_data_dir, 'no_directory_urls'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def test_alias_redirect(self):
        assertPopen(['mike', 'deploy', '1.0', 'latest',
                     '--alias-type=redirect'])
        check_call_silent(['git', 'checkout', 'gh-pages'])

        with open('latest/index.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/index.html'))
        with open('latest/page.html') as f:
            self.assertRegex(f.read(),
                             match_redir('../1.0/page.html'))
