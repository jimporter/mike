import re
import unittest
from itertools import chain
from unittest import mock

from .. import *
from .mock_server import MockRequest, MockServer
from mike import commands, git_utils, versions


class TestListVersions(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('list_versions')
        git_init()

    def test_versions_exist(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": []}]',
            ))

        self.assertEqual(list(commands.list_versions()), [
            versions.VersionInfo('1.0'),
        ])

    def test_versions_nonexistent(self):
        self.assertEqual(list(commands.list_versions()), [])


class TestBase(unittest.TestCase):
    def _test_state(self, expected_message, expected_versions):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message, expected_message)

        dirs = set()
        for i in expected_versions:
            dirs |= {str(i.version)} | i.aliases
        contents = {'versions.json'} | set(chain.from_iterable(
            (d, d + '/file.txt') for d in dirs
        ))
        assertDirectory('.', contents)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())),
                             expected_versions)


class TestDeploy(TestBase):
    def setUp(self):
        self.stage = stage_dir('deploy')
        git_init()
        commit_file('file.txt')

    def _test_deploy(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('1.0')]):
        if not expected_message:
            rev = git_utils.get_latest_commit('master', short=True)
            expected_message = (
                r'^Deployed {} to {} with MkDocs \S+ and mike \S+$'
                .format(rev, expected_versions[0].version)
            )

        self._test_state(expected_message, expected_versions)

    def test_default(self):
        commands.deploy(self.stage, '1.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        commands.deploy(self.stage, '1.0', '1.0.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.0')
        ])

    def test_aliases(self):
        commands.deploy(self.stage, '1.0', aliases=['latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])

    def test_branch(self):
        commands.deploy(self.stage, '1.0', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        commands.deploy(self.stage, '1.0', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('^commit message$')

    def test_overwrite_version(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": ["latest"]}]',
            ))
            commit.add_file(git_utils.FileInfo('1.0/old-file.txt', ''))
            commit.add_file(git_utils.FileInfo('latest/old-file.txt', ''))

        commands.deploy(self.stage, '1.0', '1.0.1', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest', 'greatest'])
        ])

    def test_overwrite_alias(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": ["latest"]}]',
            ))
            commit.add_file(git_utils.FileInfo('1.0/file.txt', ''))
            commit.add_file(git_utils.FileInfo('latest/file.txt', ''))

        with self.assertRaises(ValueError):
            commands.deploy(self.stage, '2.0', '2.0.0', ['latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('add versions.json', [
            versions.VersionInfo('1.0', '1.0', ['latest'])
        ])

    def test_update_aliases(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": ["latest"]}]',
            ))
            commit.add_file(git_utils.FileInfo('1.0/file.txt', ''))
            commit.add_file(git_utils.FileInfo('latest/file.txt', ''))

        commands.deploy(self.stage, '2.0', '2.0.0', ['latest'], True)
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('.*', [
            versions.VersionInfo('2.0', '2.0.0', ['latest']),
            versions.VersionInfo('1.0', '1.0', []),
        ])


class TestDelete(TestBase):
    def setUp(self):
        self.stage = stage_dir('delete')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', aliases=['stable'], branch=branch)
        commands.deploy(self.stage, '2.0', branch=branch)

    def _test_delete(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('2.0')]):
        if not expected_message:
            expected_message = r'^Removed \S+ with mike \S+$'

        self._test_state(expected_message, expected_versions)

    def test_delete_version(self):
        self._deploy()
        commands.delete(['1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_delete_alias(self):
        self._deploy()
        commands.delete(['stable'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete(expected_versions=[
            versions.VersionInfo('2.0'),
            versions.VersionInfo('1.0'),
        ])

    def test_delete_all(self):
        self._deploy()
        commands.delete(all=True)
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message, r'^Removed everything with mike \S+$')
        assertDirectory('.', set())

    def test_branch(self):
        self._deploy('branch')
        commands.delete(['1.0'], branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_delete()

    def test_commit_message(self):
        self._deploy()
        commands.delete(['1.0'], message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete('^commit message$')

    def test_delete_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.delete)
        self.assertRaises(ValueError, commands.delete, ['3.0'])
        self.assertRaises(ValueError, commands.delete, ['1.0'],
                          branch='branch')


class TestAlias(TestBase):
    def setUp(self):
        self.stage = stage_dir('alias')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', aliases=['latest'], branch=branch)

    def _test_alias(self, expected_message=None, expected_src='1.0',
                    expected_aliases=['greatest']):
        if not expected_message:
            expected_message = r'^Copied {} to {} with mike \S+$'.format(
                re.escape(expected_src),
                re.escape(', '.join(expected_aliases))
            )

        self._test_state(expected_message, [
            versions.VersionInfo('1.0', aliases=expected_aliases + ['latest'])
        ])

    def test_alias_from_version(self):
        self._deploy()
        commands.alias('1.0', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

    def test_alias_from_alias(self):
        self._deploy()
        commands.alias('latest', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(expected_src='latest')

    def xtest_delete_all(self):
        self._deploy()
        commands.delete(all=True)
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message, r'^Removed everything with mike \S+$')
        assertDirectory('.', set())

    def test_branch(self):
        self._deploy('branch')
        commands.alias('1.0', ['greatest'], branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_alias()

    def test_commit_message(self):
        self._deploy()
        commands.alias('1.0', ['greatest'], message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias('^commit message$')

    def test_alias_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.alias, '2.0', ['alias'])
        self.assertRaises(ValueError, commands.alias, '1.0', ['alias'],
                          branch='branch')


class TestRetitle(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('retitle')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', branch=branch)

    def _test_retitle(self, expected_message=None):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(message,
                             r'^Set title of \S+ to 1\.0\.1 with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '1.0',
            '1.0/file.txt'
        })
        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', '1.0.1'),
            ])

    def test_retitle(self):
        self._deploy()
        commands.retitle('1.0', '1.0.1')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle()

    def test_branch(self):
        self._deploy('branch')
        commands.retitle('1.0', '1.0.1', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_retitle()

    def test_commit_message(self):
        self._deploy()
        commands.retitle('1.0', '1.0.1', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle('commit message')

    def test_retitle_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.retitle, '2.0', '2.0.2')
        self.assertRaises(ValueError, commands.retitle, '1.0', '1.0.1',
                          branch='branch')


class TestSetDefault(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('set_default')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', branch=branch)

    def _test_default(self, expected_message=None):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(message,
                             r'^Set default version to \S+ with mike \S+$')

        with open('index.html') as f:
            self.assertRegex(f.read(), r'window\.location\.replace\("1\.0"\)')

    def test_set_default(self):
        self._deploy()
        commands.set_default('1.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_branch(self):
        self._deploy('branch')
        commands.set_default('1.0', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_default()

    def test_commit_message(self):
        self._deploy()
        commands.set_default('1.0', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default('commit message')

    def test_set_invalid_default(self):
        self._deploy()
        self.assertRaises(ValueError, commands.set_default, '2.0')
        self.assertRaises(ValueError, commands.set_default, '1.0',
                          branch='branch')


class TestServe(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('serve')
        git_init()
        with git_utils.Commit('branch', 'add file') as commit:
            commit.add_file(git_utils.FileInfo('index.html', 'main page'))
            commit.add_file(git_utils.FileInfo('dir/index.html', 'sub page'))

    def test_serve(self):
        class MyMockServer(MockServer):
            def serve_forever(self):
                self.handle_request(MockRequest())
                raise KeyboardInterrupt()

        handler_name = 'mike.server.GitBranchHTTPHandler'
        with mock.patch('http.server.HTTPServer', MyMockServer), \
             mock.patch(handler_name + '.wbufsize', -1), \
             mock.patch(handler_name + '.log_message') as m:  # noqa
            commands.serve(branch='branch', verbose=False)
            self.assertEqual(m.call_args[0][1:3], ('GET / HTTP/1.1', '200'))
