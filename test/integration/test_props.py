import os
import unittest

from . import assertPopen, assertOutput
from .. import *
from mike import git_utils, versions


class PropsTestCase(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir(self.stage_dir)
        git_init()
        copytree(os.path.join(test_data_dir, 'basic_theme'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _add_version(self, version='1.0', aliases=[], properties=None,
                     branch='gh-pages', deploy_prefix=''):
        all_versions = versions.Versions()
        all_versions.add(version, aliases=aliases)
        all_versions[version].properties = properties

        with git_utils.Commit(branch, 'commit message') as commit:
            commit.add_file(git_utils.FileInfo(
                os.path.join(deploy_prefix, 'versions.json'),
                all_versions.dumps()
            ))

    def _test_set_props(self, expected_versions=[versions.VersionInfo(
        '1.0', properties={'hidden': True}
    )], expected_message=None, directory='.'):
        message = assertPopen(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Set properties for {}( in .*)? with mike \S+$'
                .format(expected_versions[0].version)
            )

        with open(os.path.join(directory, 'versions.json')) as f:
            self.assertEqual(list(versions.Versions.loads(f.read())),
                             expected_versions)


class TestGetProp(PropsTestCase):
    stage_dir = 'get_prop'

    def test_get_prop(self):
        self._add_version(properties={'hidden': True})
        assertOutput(self, ['mike', 'props', '1.0', 'hidden'], 'true\n')

    def test_branch(self):
        self._add_version(properties={'hidden': True}, branch='branch')
        assertOutput(self, ['mike', 'props', '-b', 'branch', '1.0', 'hidden'],
                     'true\n')

    def test_from_subdir(self):
        self._add_version(properties={'hidden': True})
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'props', '1.0', 'hidden'], returncode=1)
            assertOutput(self, ['mike', 'props', '1.0', 'hidden',
                                '-F', '../mkdocs.yml'], 'true\n')

    def test_from_subdir_explicit_branch(self):
        self._add_version(properties={'hidden': True})
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'props', '1.0', 'hidden'], returncode=1)
            assertOutput(self, ['mike', 'props', '1.0', 'hidden',
                                '-b', 'gh-pages', '-r', 'origin'], 'true\n')

    def test_deploy_prefix(self):
        self._add_version(properties={'hidden': True}, deploy_prefix='prefix')
        assertOutput(self, ['mike', 'props', '1.0', 'hidden',
                            '--deploy-prefix', 'prefix'], 'true\n')

    def test_ahead_remote(self):
        self._add_version()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('get_prop_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._add_version(properties={'hidden': True})
        clone_rev = git_utils.get_latest_commit('gh-pages')

        assertOutput(self, ['mike', 'props', '1.0', 'hidden'], 'true\n')
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_behind_remote(self):
        self._add_version()
        stage_dir('get_prop_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._add_version(properties={'hidden': True})
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'props', '1.0', 'hidden'], 'true\n')
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), origin_rev)

    def test_diverged_remote(self):
        self._add_version()
        stage_dir('get_prop_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._add_version(properties={'hidden': True})

        self._add_version(properties={'hidden': False})
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(self, ['mike', 'props', '1.0', 'hidden'],
                     stdout='false\n',
                     stderr=('warning: gh-pages has diverged from ' +
                             'origin/gh-pages\n'))
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertOutput(self, ['mike', 'props', '1.0', 'hidden',
                            '--ignore-remote-status'],
                     stdout='false\n', stderr='')
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

    def test_get_and_set(self):
        self._add_version(properties={'hidden': True})
        assertOutput(
            self, ['mike', 'props', '1.0', 'hidden', '--set', 'dev=true'],
            stdout='', stderr=('error: cannot get and set properties at the ' +
                               'same time\n'),
            returncode=1
        )


class TestSetProps(PropsTestCase):
    stage_dir = 'set_props'

    def test_set_prop(self):
        self._add_version()
        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props()

    def test_set_string_prop(self):
        self._add_version()
        assertPopen(['mike', 'props', '1.0', '--set-string', 'kind=dev'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props(expected_versions=[versions.VersionInfo(
            '1.0', properties={'kind': 'dev'}
        )])

    def test_set_all_props(self):
        self._add_version()
        assertPopen(['mike', 'props', '1.0', '--set-all', '{"hidden": true}'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props()

    def test_delete_prop(self):
        self._add_version(properties={'hidden': True, 'kind': 'dev'})
        assertPopen(['mike', 'props', '1.0', '--delete', 'kind'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props()

    def test_delete_all_props(self):
        self._add_version(properties={'hidden': True, 'kind': 'dev'})
        assertPopen(['mike', 'props', '1.0', '--delete-all'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props(expected_versions=[versions.VersionInfo('1.0')])

    def test_branch(self):
        self._add_version(branch='branch')
        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                     '-b', 'branch'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_set_props()

    def test_from_subdir(self):
        self._add_version()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'],
                        returncode=1)
            assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                         '-F', '../mkdocs.yml'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props()

    def test_from_subdir_explicit_branch(self):
        self._add_version()
        os.mkdir('sub')
        with pushd('sub'):
            assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                         '-b', 'gh-pages', '-r', 'origin'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props()

    def test_commit_message(self):
        self._add_version()
        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                     '-m', 'commit message'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props(expected_message='commit message')

    def test_deploy_prefix(self):
        self._add_version(deploy_prefix='prefix')
        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                     '--deploy-prefix', 'prefix'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_set_props(directory='prefix')

    def test_push(self):
        self._add_version()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true', '-p'])
        clone_rev = git_utils.get_latest_commit('gh-pages')

        with pushd(self.stage):
            origin_rev = git_utils.get_latest_commit('gh-pages')
            self.assertEqual(origin_rev, clone_rev)

    def test_remote_empty(self):
        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        self._add_version()
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)

    def test_local_empty(self):
        self._add_version()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_ahead_remote(self):
        self._add_version()
        origin_rev = git_utils.get_latest_commit('gh-pages')

        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        self._add_version(properties={'hidden': True})
        old_rev = git_utils.get_latest_commit('gh-pages')

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), old_rev)
        self.assertEqual(git_utils.get_latest_commit('gh-pages^^'), origin_rev)

    def test_behind_remote(self):
        self._add_version()

        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._add_version(properties={'hidden': True})
            origin_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), origin_rev)

    def test_diverged_remote(self):
        self._add_version()

        stage_dir('set_props_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        check_call_silent(['git', 'fetch', 'origin', 'gh-pages:gh-pages'])
        git_config()

        with pushd(self.stage):
            self._add_version(properties={'hidden': True})

        self._add_version(properties={'hidden': False})
        clone_rev = git_utils.get_latest_commit('gh-pages')
        check_call_silent(['git', 'fetch', 'origin'])

        assertOutput(
            self, ['mike', 'props', '1.0', '--set', 'hidden=true'],
            stdout='', stderr=(
                'error: gh-pages has diverged from origin/gh-pages\n' +
                "  If you're sure this is intended, retry with " +
                '--ignore-remote-status\n'
            ), returncode=1
        )
        self.assertEqual(git_utils.get_latest_commit('gh-pages'), clone_rev)

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true',
                     '--ignore-remote-status'])
        self.assertEqual(git_utils.get_latest_commit('gh-pages^'), clone_rev)


class TestSetPropsOtherRemote(PropsTestCase):
    def _deploy(self, branch=None, versions=['1.0'], deploy_prefix=''):
        extra_args = ['-b', branch] if branch else []
        if deploy_prefix:
            extra_args.extend(['--deploy-prefix', deploy_prefix])
        for i in versions:
            assertPopen(['mike', 'deploy', i] + extra_args)

    def setUp(self):
        self.stage_origin = stage_dir('set_props_remote')
        git_init()
        copytree(os.path.join(test_data_dir, 'remote'), self.stage_origin)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])

    def _clone(self):
        self.stage = stage_dir('set_props_remote_clone')
        check_call_silent(['git', 'clone', self.stage_origin, '.'])
        git_config()

    def _test_rev(self, branch):
        clone_rev = git_utils.get_latest_commit(branch)
        with pushd(self.stage_origin):
            self.assertEqual(git_utils.get_latest_commit(branch), clone_rev)

    def test_default(self):
        self._add_version(branch='mybranch')
        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=false'])
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true', '-p'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_set_props()
        self._test_rev('mybranch')

    def test_explicit_branch(self):
        self._add_version(branch='pages')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'myremote'])

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true', '-p',
                     '-b', 'pages'])
        check_call_silent(['git', 'checkout', 'pages'])
        self._test_set_props()
        self._test_rev('pages')

    def test_explicit_remote(self):
        self._add_version(branch='mybranch')
        self._clone()
        check_call_silent(['git', 'remote', 'rename', 'origin', 'remote'])

        assertPopen(['mike', 'props', '1.0', '--set', 'hidden=true', '-p',
                     '-r', 'remote'])
        check_call_silent(['git', 'checkout', 'mybranch'])
        self._test_set_props()
        self._test_rev('mybranch')
