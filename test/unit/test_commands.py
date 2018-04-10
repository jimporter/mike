from __future__ import unicode_literals

import mock
import os
import ruamel.yaml as yaml
import subprocess
import unittest
from itertools import chain
from six import assertRegex

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


class TestDeploy(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('deploy')
        git_init()
        commit_file('file.txt')

    def _test_deploy(self, expected_message=None,
                     version=versions.VersionInfo('1.0')):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(
                self, message,
                r'^Deployed \S+ to 1.0 with MkDocs \S+ and mike \S+$'
            )

        dirs = {str(version.version)} | version.aliases
        contents = {'versions.json'} | set(chain.from_iterable(
            (d, d + '/file.txt') for d in dirs
        ))
        assertDirectory('.', contents)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                version,
            ])

    def test_default(self):
        commands.deploy(self.stage, '1.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        commands.deploy(self.stage, '1.0', '1.0.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(version=versions.VersionInfo('1.0', '1.0.0'))

    def test_aliases(self):
        commands.deploy(self.stage, '1.0', aliases=['latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(version=versions.VersionInfo(
            '1.0', aliases=['latest']
        ))

    def test_branch(self):
        commands.deploy(self.stage, '1.0', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        commands.deploy(self.stage, '1.0', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('commit message')


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('delete')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', branch=branch)
        commands.deploy(self.stage, '2.0', branch=branch)

    def _test_delete(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message, r'^Removed \S+ with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '2.0',
            '2.0/file.txt'
        })
        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('2.0'),
            ])

    def test_delete_versions(self):
        self._deploy()
        commands.delete(['1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete()

    def test_delete_all(self):
        self._deploy()
        commands.delete(all=True)
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        assertRegex(self, message, r'^Removed everything with mike \S+$')
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
        self._test_delete('commit message')

    def test_delete_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.delete)
        self.assertRaises(ValueError, commands.delete, ['3.0'])
        self.assertRaises(ValueError, commands.delete, ['1.0'],
                          branch='branch')


class TestRename(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('rename')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', branch=branch)

    def _test_rename(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message, r'^Set title of version \S+ to ' +
                        r'1\.0\.1 with mike \S+$')

        assertDirectory('.', {
            'versions.json',
            '1.0',
            '1.0/file.txt'
        })
        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                versions.VersionInfo('1.0', '1.0.1'),
            ])

    def test_rename(self):
        self._deploy()
        commands.rename('1.0', '1.0.1')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_rename()

    def test_branch(self):
        self._deploy('branch')
        commands.rename('1.0', '1.0.1', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_rename()

    def test_commit_message(self):
        self._deploy()
        commands.rename('1.0', '1.0.1', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_rename('commit message')

    def test_rename_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.rename, '2.0', '2.0.2')
        self.assertRaises(ValueError, commands.rename, '1.0', '1.0.1',
                          branch='branch')


class TestSetDefault(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('set_default')
        git_init()
        commit_file('file.txt')

    def _deploy(self, branch='gh-pages'):
        commands.deploy(self.stage, '1.0', branch=branch)

    def _test_default(self, expected_message=None):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(self, message,
                        r'^Set default version to \S+ with mike \S+$')

        with open('index.html') as f:
            assertRegex(self, f.read(),
                        r'window\.location\.replace\("1\.0"\)')

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


class TestGetThemeDir(unittest.TestCase):
    def test_mkdocs_theme(self):
        theme_dir = commands.get_theme_dir('mkdocs')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_bootswatch_theme(self):
        theme_dir = commands.get_theme_dir('yeti')
        self.assertEqual(os.path.basename(theme_dir), 'mkdocs')

    def test_unknown_theme(self):
        self.assertRaises(ValueError, commands.get_theme_dir, 'nonexist')

    def test_no_theme(self):
        self.assertRaises(ValueError, commands.get_theme_dir, None)


class TestMakeDirs(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('makedirs')

    def test_nonexistent(self):
        commands._makedirs('dir')
        assertDirectory('.', {'dir'})

    def test_existing_dir(self):
        os.mkdir('dir')
        commands._makedirs('dir')
        assertDirectory('.', {'dir'})

    def test_existing_file(self):
        open('dir', 'w').close()
        self.assertRaises(OSError, commands._makedirs, 'dir')


class TestInstallExtras(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('install_extras')
        self.mkdocs_yml = os.path.join(self.stage, 'mkdocs.yml')

    def _test_extras(self):
        assertDirectory('.', {
            'mkdocs.yml',
            'docs',
            'docs/css',
            'docs/css/version-select.css',
            'docs/js',
            'docs/js/version-select.js',
            'docs/index.md',
        })

        with open(self.mkdocs_yml) as f:
            config = yaml.safe_load(f)
            self.assertTrue(os.path.join('css', 'version-select.css') in
                            config['extra_css'])
            self.assertTrue(os.path.join('js', 'version-select.js') in
                            config['extra_javascript'])

    def test_mkdocs_theme(self):
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        commands.install_extras(self.mkdocs_yml)
        self._test_extras()

    def test_no_theme(self):
        copytree(os.path.join(test_data_dir, 'no_theme'), self.stage)
        self.assertRaises(ValueError, commands.install_extras, self.mkdocs_yml)
        commands.install_extras(self.mkdocs_yml, theme='mkdocs')
        self._test_extras()

    def test_install_twice(self):
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        commands.install_extras(self.mkdocs_yml)
        commands.install_extras(self.mkdocs_yml)
        self._test_extras()


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
        with mock.patch('six.moves.BaseHTTPServer.HTTPServer', MyMockServer), \
             mock.patch(handler_name + '.wbufsize', -1), \
             mock.patch(handler_name + '.log_message') as m:  # noqa
            commands.serve(branch='branch', verbose=False)
            self.assertEqual(m.call_args[0][1:3], ('GET / HTTP/1.1', '200'))
