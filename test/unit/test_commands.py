import os
import re
import shutil
import unittest
from collections.abc import Collection
from unittest import mock

from .. import *
from .mock_server import MockRequest, MockServer
from mike import commands, git_utils, versions


def match_redir(url):
    return r'window\.location\.replace\("{}"\)'.format(re.escape(url))


class MockConfig:
    def __init__(self, site_dir, remote_name='origin',
                 remote_branch='gh-pages', use_directory_urls=True):
        self.site_dir = site_dir
        self.remote_name = remote_name
        self.remote_branch = remote_branch
        self.use_directory_urls = use_directory_urls


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
    def setUp(self):
        self.stage = stage_dir(self.stage_dir)
        self.cfg = MockConfig(self.stage)
        git_init()
        commit_files(['page.html', 'file.txt', 'dir/index.html'])

    def _test_state(self, expected_message, expected_versions, redirect=True,
                    directory='.'):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message, expected_message)

        files = {'versions.json'}
        for v in expected_versions:
            vstr = str(v.version)
            files |= {vstr, vstr + '/page.html', vstr + '/file.txt',
                      vstr + '/dir', vstr + '/dir/index.html'}
            for a in v.aliases:
                files |= {a, a + '/page.html', a + '/dir',
                          a + '/dir/index.html'}
                if ( redirect is False or
                     (isinstance(redirect, Collection) and
                      a not in redirect) ):
                    files.add(a + '/file.txt')
        assertDirectory(directory, files)

        with open(os.path.join(directory, 'versions.json')) as f:
            self.assertEqual(list(versions.Versions.loads(f.read())),
                             expected_versions)


class TestDeploy(TestBase):
    stage_dir = 'deploy'

    def setUp(self):
        super().setUp()
        self.cfg.site_dir = os.path.join(self.cfg.site_dir, 'site')

    def _mock_build(self):
        copytree(self.stage, self.cfg.site_dir)

    def _test_deploy(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('1.0')],
                     **kwargs):
        if not expected_message:
            rev = git_utils.get_latest_commit('master', short=True)
            expected_message = (
                r'^Deployed {} to {}( in .*)? with MkDocs \S+ and mike \S+$'
                .format(rev, expected_versions[0].version)
            )

        if os.path.exists(self.cfg.site_dir):
            shutil.rmtree(self.cfg.site_dir)
        self._test_state(expected_message, expected_versions, **kwargs)

    def _mock_commit(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": ["latest"]}]',
            ))
            commit.add_file(git_utils.FileInfo('1.0/page.html', ''))
            commit.add_file(git_utils.FileInfo('1.0/file.txt', ''))
            commit.add_file(git_utils.FileInfo('1.0/dir/index.html', ''))
            commit.add_file(git_utils.FileInfo('latest/page.html', ''))
            commit.add_file(git_utils.FileInfo('latest/dir/index.html', ''))

    def test_default(self):
        with commands.deploy(self.cfg, '1.0'):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        with commands.deploy(self.cfg, '1.0', '1.0.0'):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.0')
        ])

    def test_aliases(self):
        with commands.deploy(self.cfg, '1.0', aliases=['latest']):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])

        with open('latest/page.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/page.html'))
        with open('latest/dir/index.html') as f:
            self.assertRegex(f.read(), match_redir('../../1.0/dir/'))

    def test_aliases_no_directory_urls(self):
        self.cfg.use_directory_urls = False
        with commands.deploy(self.cfg, '1.0', aliases=['latest']):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])

        with open('latest/page.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/page.html'))
        with open('latest/dir/index.html') as f:
            self.assertRegex(f.read(), match_redir('../../1.0/dir/index.html'))

    def test_aliases_copy(self):
        with commands.deploy(self.cfg, '1.0', aliases=['latest'],
                             redirect=False):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ], redirect=False)

    def test_aliases_custom_redirect(self):
        real_open = open
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=b'{{href}}')):
            with commands.deploy(self.cfg, '1.0', aliases=['latest'],
                                 template='template.html'):
                # Un-mock `open` so we can copy files for real.
                with mock.patch('builtins.open', real_open):
                    self._mock_build()

        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ])

        with open('latest/page.html') as f:
            self.assertEqual(f.read(), '../1.0/page.html')
        with open('latest/dir/index.html') as f:
            self.assertEqual(f.read(), '../../1.0/dir/')

    def test_branch(self):
        with commands.deploy(self.cfg, '1.0', branch='branch'):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        with commands.deploy(self.cfg, '1.0', message='commit message'):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('^commit message$')

    def test_prefix(self):
        with commands.deploy(self.cfg, '1.0', aliases=['latest'],
                             prefix='prefix'):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', aliases=['latest'])
        ], directory='prefix')

    def test_overwrite_version(self):
        with git_utils.Commit('gh-pages', 'add versions.json') as commit:
            commit.add_file(git_utils.FileInfo(
                'versions.json',
                '[{"version": "1.0", "title": "1.0", "aliases": ["latest"]}]',
            ))
            commit.add_file(git_utils.FileInfo('1.0/old-page.html', ''))
            commit.add_file(git_utils.FileInfo('latest/old-page.html', ''))

        with commands.deploy(self.cfg, '1.0', '1.0.1', ['greatest']):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest', 'greatest'])
        ])

    def test_overwrite_same_alias(self):
        self._mock_commit()
        with commands.deploy(self.cfg, '1.0', '1.0.1', ['latest']):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest'])
        ])

    def test_overwrite_include_same_alias(self):
        self._mock_commit()
        with commands.deploy(self.cfg, '1.0', '1.0.1', ['latest', 'greatest']):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(expected_versions=[
            versions.VersionInfo('1.0', '1.0.1', ['latest', 'greatest'])
        ])

    def test_overwrite_alias_error(self):
        self._mock_commit()
        with self.assertRaises(ValueError):
            with commands.deploy(self.cfg, '2.0', '2.0.0', ['latest']):
                raise AssertionError('should not get here')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('add versions.json', [
            versions.VersionInfo('1.0', '1.0', ['latest'])
        ])

    def test_update_aliases(self):
        self._mock_commit()
        with commands.deploy(self.cfg, '2.0', '2.0.0', ['latest'],
                             update_aliases=True):
            self._mock_build()
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('.*', [
            versions.VersionInfo('2.0', '2.0.0', ['latest']),
            versions.VersionInfo('1.0', '1.0', []),
        ])


class TestDelete(TestBase):
    stage_dir = 'delete'

    def _deploy(self, branch='gh-pages', prefix=''):
        with commands.deploy(self.cfg, '1.0', aliases=['stable'],
                             branch=branch, prefix=prefix):
            pass
        with commands.deploy(self.cfg, '2.0', branch=branch, prefix=prefix):
            pass

    def _test_delete(self, expected_message=None,
                     expected_versions=[versions.VersionInfo('2.0')],
                     **kwargs):
        if not expected_message:
            expected_message = r'^Removed \S+( in .*)? with mike \S+$'

        self._test_state(expected_message, expected_versions, **kwargs)

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

    def test_prefix(self):
        self._deploy(prefix='prefix')
        commands.delete(['1.0'], prefix='prefix')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_delete(directory='prefix')

    def test_prefix_delete_all(self):
        self._deploy(prefix='prefix')
        commands.delete(all=True, prefix='prefix')
        check_call_silent(['git', 'checkout', 'gh-pages'])

        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        self.assertRegex(message,
                         r'^Removed everything in prefix with mike \S+$')
        assertDirectory('prefix', set())

    def test_delete_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.delete)
        self.assertRaises(ValueError, commands.delete, ['3.0'])
        self.assertRaises(ValueError, commands.delete, ['1.0'],
                          branch='branch')


class TestAlias(TestBase):
    stage_dir = 'alias'

    def _deploy(self, branch='gh-pages', prefix=''):
        with commands.deploy(self.cfg, '1.0', aliases=['latest'],
                             branch=branch, prefix=prefix):
            pass

    def _test_alias(self, expected_message=None, expected_src='1.0',
                    expected_aliases=['greatest'], **kwargs):
        if not expected_message:
            expected_message = (
                r'^Copied {} to {}( in .*)? with mike \S+$'
                .format(re.escape(expected_src),
                        re.escape(', '.join(expected_aliases)))
            )

        self._test_state(expected_message, [
            versions.VersionInfo('1.0', aliases=expected_aliases + ['latest'])
        ], **kwargs)

    def test_alias_from_version(self):
        self._deploy()
        commands.alias(self.cfg, '1.0', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

        with open('greatest/page.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/page.html'))
        with open('greatest/dir/index.html') as f:
            self.assertRegex(f.read(), match_redir('../../1.0/dir/'))

    def test_alias_no_directory_urls(self):
        self._deploy()
        self.cfg.use_directory_urls = False
        commands.alias(self.cfg, '1.0', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

        with open('greatest/page.html') as f:
            self.assertRegex(f.read(), match_redir('../1.0/page.html'))
        with open('greatest/dir/index.html') as f:
            self.assertRegex(f.read(), match_redir('../../1.0/dir/index.html'))

    def test_alias_from_alias(self):
        self._deploy()
        commands.alias(self.cfg, 'latest', ['greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

    def test_alias_copy(self):
        self._deploy()
        commands.alias(self.cfg, '1.0', ['greatest'], redirect=False)
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(redirect=['latest'])

    def test_alias_custom_redirect(self):
        self._deploy()
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=b'{{href}}')):
            commands.alias(self.cfg, '1.0', ['greatest'],
                           template='template.html')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias()

        with open('greatest/page.html') as f:
            self.assertEqual(f.read(), '../1.0/page.html')
        with open('greatest/dir/index.html') as f:
            self.assertEqual(f.read(), '../../1.0/dir/')

    def test_alias_overwrite_same(self):
        self._deploy()
        commands.alias(self.cfg, '1.0', ['latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(expected_aliases=['latest'])

    def test_alias_overwrite_include_same(self):
        self._deploy()
        commands.alias(self.cfg, '1.0', ['latest', 'greatest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(expected_aliases=['latest', 'greatest'])

    def test_alias_overwrite_error(self):
        self._deploy()
        with commands.deploy(self.cfg, '2.0'):
            pass
        with self.assertRaises(ValueError):
            commands.alias(self.cfg, '2.0', ['latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_state(r'^Deployed \w+ to 2\.0', [
            versions.VersionInfo('2.0', '2.0'),
            versions.VersionInfo('1.0', '1.0', ['latest']),
        ])

    def test_alias_update(self):
        self._deploy()
        with commands.deploy(self.cfg, '2.0'):
            pass
        commands.alias(self.cfg, '2.0', ['latest'], update_aliases=True)
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_state(r'^Copied 2\.0 to latest', [
            versions.VersionInfo('2.0', '2.0', ['latest']),
            versions.VersionInfo('1.0', '1.0'),
        ])

    def test_branch(self):
        self._deploy('branch')
        commands.alias(self.cfg, '1.0', ['greatest'], branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_alias()

    def test_commit_message(self):
        self._deploy()
        commands.alias(self.cfg, '1.0', ['greatest'], message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias('^commit message$')

    def test_prefix(self):
        self._deploy(prefix='prefix')
        commands.alias(self.cfg, '1.0', ['greatest'], prefix='prefix')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_alias(directory='prefix')

    def test_alias_invalid_version(self):
        self._deploy()
        self.assertRaises(ValueError, commands.alias, self.cfg, '2.0',
                          ['alias'])
        self.assertRaises(ValueError, commands.alias, self.cfg, '1.0',
                          ['alias'], branch='branch')


class TestRetitle(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('retitle')
        self.cfg = MockConfig(self.stage)
        git_init()
        commit_files(['file.txt'])

    def _deploy(self, branch='gh-pages', prefix=''):
        with commands.deploy(self.cfg, '1.0', branch=branch, prefix=prefix):
            pass

    def _test_retitle(self, expected_message=None, directory='.'):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Set title of \S+ to 1\.0\.1( in .*)? with mike \S+$'
            )

        assertDirectory(directory, {
            'versions.json',
            '1.0',
            '1.0/file.txt'
        })
        with open(os.path.join(directory, 'versions.json')) as f:
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

    def test_prefix(self):
        self._deploy(prefix='prefix')
        commands.retitle('1.0', '1.0.1', prefix='prefix')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_retitle(directory='prefix')

    def test_retitle_invalid(self):
        self._deploy()
        self.assertRaises(ValueError, commands.retitle, '2.0', '2.0.2')
        self.assertRaises(ValueError, commands.retitle, '1.0', '1.0.1',
                          branch='branch')


class TestSetDefault(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('set_default')
        self.cfg = MockConfig(self.stage)
        git_init()
        commit_files(['file.txt'])

    def _deploy(self, branch='gh-pages', prefix=''):
        with commands.deploy(self.cfg, '1.0', branch=branch, prefix=prefix):
            pass

    def _test_default(self, expr=r'window\.location\.replace\("1\.0/"\)',
                      expected_message=None, directory='.'):
        message = check_output(['git', 'log', '-1', '--pretty=%B']).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            self.assertRegex(
                message,
                r'^Set default version to \S+( in .*)? with mike \S+$'
            )

        with open(os.path.join(directory, 'index.html')) as f:
            self.assertRegex(f.read(), expr)

    def test_set_default(self):
        self._deploy()
        commands.set_default('1.0')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default()

    def test_custom_template(self):
        self._deploy()
        with mock.patch('builtins.open',
                        mock.mock_open(read_data=b'{{href}}')):
            commands.set_default('1.0', 'template.html')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default(r'^1\.0/$')

    def test_branch(self):
        self._deploy('branch')
        commands.set_default('1.0', branch='branch')
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_default()

    def test_commit_message(self):
        self._deploy()
        commands.set_default('1.0', message='commit message')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default(expected_message='commit message')

    def test_prefix(self):
        self._deploy(prefix='prefix')
        commands.set_default('1.0', prefix='prefix')
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_default(directory='prefix')

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
