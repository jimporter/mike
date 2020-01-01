import os
import subprocess
import sys
import unittest

from .. import *
from mike import git_utils


class TestMakeWhen(unittest.TestCase):
    def test_default(self):
        self.assertRegex(git_utils.make_when(), r'\d+ (\+|-)\d{4}')

    def test_timestamp(self):
        self.assertRegex(git_utils.make_when(12345), r'12345 (\+|-)\d{4}')


class TestGetConfig(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('get_config')
        git_init()

    def test_get_username(self):
        self.assertEqual(git_utils.get_config('user.name'), 'username')

    def test_get_email(self):
        self.assertEqual(git_utils.get_config('user.email'), 'user@site.tld')

    def test_get_unknown(self):
        self.assertRaises(git_utils.GitError, git_utils.get_config, 'nonexist')


class TestGetLatestCommit(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('get_latest_commit')
        git_init()
        commit_file('file.txt', 'initial commit')

    def test_latest_commit(self):
        rev = git_utils.get_latest_commit('master')
        expected_rev = (subprocess.check_output(
            ['git', 'rev-parse', 'master'], universal_newlines=True
        ).rstrip())
        self.assertEqual(rev, expected_rev)

    def test_short(self):
        rev = git_utils.get_latest_commit('master', short=True)
        expected_rev = (subprocess.check_output(
            ['git', 'rev-parse', 'master'], universal_newlines=True
        ).rstrip())
        self.assertEqual(rev, expected_rev[0:len(rev)])

    def test_nonexistent_branch(self):
        self.assertRaises(git_utils.GitError, git_utils.get_latest_commit,
                          'nonexist')


class TestGetMergeBaseAndCompareBranches(unittest.TestCase):
    def setUp(self):
        self.origin = stage_dir('get_merge_base')
        git_init()
        commit_file('file.txt', 'initial commit')
        check_call_silent(['git', 'checkout', '-b', 'branch'])

    def test_even(self):
        rev = git_utils.get_latest_commit('master')
        self.assertEqual(git_utils.get_merge_base('branch', 'master'), rev)
        self.assertEqual(git_utils.compare_branches('branch', 'master'),
                         git_utils.BranchStatus.even)

    def test_ahead(self):
        rev = git_utils.get_latest_commit('master')
        commit_file('file2.txt', 'second commit')

        self.assertEqual(git_utils.get_merge_base('branch', 'master'), rev)
        self.assertEqual(git_utils.compare_branches('branch', 'master'),
                         git_utils.BranchStatus.ahead)

    def test_behind(self):
        rev = git_utils.get_latest_commit('master')
        check_call_silent(['git', 'checkout', 'master'])
        commit_file('file2.txt', 'second commit')

        self.assertEqual(git_utils.get_merge_base('branch', 'master'), rev)
        self.assertEqual(git_utils.compare_branches('branch', 'master'),
                         git_utils.BranchStatus.behind)

    def test_diverged(self):
        rev = git_utils.get_latest_commit('master')
        commit_file('file2.txt', 'second commit')
        check_call_silent(['git', 'checkout', 'master'])
        commit_file('file2-master.txt', 'second commit')

        self.assertEqual(git_utils.get_merge_base('master', 'branch'), rev)
        self.assertEqual(git_utils.compare_branches('master', 'branch'),
                         git_utils.BranchStatus.diverged)

    def test_unrelated(self):
        check_call_silent(['git', 'checkout', '--orphan', 'orphan'])
        commit_file('file-unrelated.txt', 'new commit')

        self.assertRaises(git_utils.GitRevUnrelated, git_utils.get_merge_base,
                          'master', 'orphan')
        self.assertRaises(git_utils.GitRevUnrelated,
                          git_utils.compare_branches, 'master', 'orphan')

    def test_nonexistent_branch(self):
        self.assertRaises(git_utils.GitError, git_utils.get_merge_base,
                          'nonexist', 'nonexist')


class TestUpdateRef(unittest.TestCase):
    def setUp(self):
        self.origin = stage_dir('update_ref')
        git_init()
        commit_file('file.txt', 'initial commit')
        check_call_silent(['git', 'checkout', '-b', 'branch'])

    def test_ahead(self):
        commit_file('file2.txt', 'second commit')

        rev = git_utils.get_latest_commit('master')
        git_utils.update_ref('branch', rev)
        self.assertEqual(git_utils.get_latest_commit('branch'), rev)

    def test_behind(self):
        check_call_silent(['git', 'checkout', 'master'])
        commit_file('file2.txt', 'second commit')

        rev = git_utils.get_latest_commit('master')
        git_utils.update_ref('branch', rev)
        self.assertEqual(git_utils.get_latest_commit('branch'), rev)

    def test_diverged(self):
        commit_file('file2.txt', 'second commit')
        check_call_silent(['git', 'checkout', 'master'])
        commit_file('file2-master.txt', 'second commit')

        rev = git_utils.get_latest_commit('master')
        git_utils.update_ref('branch', rev)
        self.assertEqual(git_utils.get_latest_commit('branch'), rev)

    def test_nonexistent_ref(self):
        rev = git_utils.get_latest_commit('branch')
        self.assertRaises(git_utils.GitError, git_utils.update_ref,
                          'branch', 'nonexist')
        self.assertEqual(git_utils.get_latest_commit('branch'), rev)


class TestTryRebaseBranch(unittest.TestCase):
    def setUp(self):
        self.origin = stage_dir('try_rebase_branch_origin')
        git_init()
        commit_file('file.txt', 'initial commit')

        self.stage = stage_dir('try_rebase_branch')
        check_call_silent(['git', 'clone', self.origin, '.'])
        git_config()

    def test_even(self):
        old_rev = git_utils.get_latest_commit('master')

        git_utils.try_rebase_branch('origin', 'master')
        new_rev = git_utils.get_latest_commit('master')
        self.assertEqual(old_rev, new_rev)

    def test_ahead(self):
        commit_file('file2.txt', 'add file2')
        old_rev = git_utils.get_latest_commit('master')

        git_utils.try_rebase_branch('origin', 'master')
        new_rev = git_utils.get_latest_commit('master')
        self.assertEqual(old_rev, new_rev)

    def test_behind(self):
        old_rev = git_utils.get_latest_commit('master')
        with pushd(self.origin):
            commit_file('file2.txt', 'add file2')
            origin_rev = git_utils.get_latest_commit('master')
        check_call_silent(['git', 'fetch', 'origin'])

        git_utils.try_rebase_branch('origin', 'master')
        new_rev = git_utils.get_latest_commit('master')
        self.assertNotEqual(old_rev, origin_rev)
        self.assertEqual(new_rev, origin_rev)

    def test_diverged(self):
        commit_file('file2.txt', 'add file2')
        old_rev = git_utils.get_latest_commit('master')
        with pushd(self.origin):
            commit_file('file2-origin.txt', 'add file2')
        check_call_silent(['git', 'fetch', 'origin'])

        self.assertRaises(git_utils.GitBranchDiverged,
                          git_utils.try_rebase_branch, 'origin', 'master')
        new_rev = git_utils.get_latest_commit('master')
        self.assertEqual(old_rev, new_rev)

    def test_diverged_force(self):
        commit_file('file2.txt', 'add file2')
        old_rev = git_utils.get_latest_commit('master')
        with pushd(self.origin):
            commit_file('file2-origin.txt', 'add file2')
            origin_rev = git_utils.get_latest_commit('master')
        check_call_silent(['git', 'fetch', 'origin'])

        git_utils.try_rebase_branch('origin', 'master', force=True)
        new_rev = git_utils.get_latest_commit('master')
        self.assertNotEqual(old_rev, origin_rev)
        self.assertEqual(new_rev, origin_rev)

    def test_nonexistent_local(self):
        check_call_silent(['git', 'checkout', '-b', 'branch'])
        check_call_silent(['git', 'branch', '-d', 'master'])
        with pushd(self.origin):
            origin_rev = git_utils.get_latest_commit('master')

        git_utils.try_rebase_branch('origin', 'master')
        local_rev = git_utils.get_latest_commit('master')
        self.assertEqual(local_rev, origin_rev)

    def test_nonexistent_remote(self):
        old_rev = git_utils.get_latest_commit('master')
        check_call_silent(['git', 'fetch', 'origin'])
        git_utils.try_rebase_branch('upstream', 'master')
        new_rev = git_utils.get_latest_commit('master')

        self.assertEqual(old_rev, new_rev)


class TestFileInfo(unittest.TestCase):
    def test_copy(self):
        f = git_utils.FileInfo(os.path.join('dir', 'file.txt'), '')
        self.assertEqual(f.copy('destdir'), git_utils.FileInfo(
            os.path.join('destdir', 'dir', 'file.txt'), ''
        ))

    def test_copy_start(self):
        f = git_utils.FileInfo(os.path.join('dir', 'file.txt'), '')
        self.assertEqual(f.copy('destdir', 'dir'), git_utils.FileInfo(
            os.path.join('destdir', 'file.txt'), ''
        ))


class TestCommit(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('commit')
        git_init()

    def _add_file(self, name, branch='master'):
        with git_utils.Commit(branch, 'add file') as commit:
            commit.add_file(git_utils.FileInfo(name, 'this is some text'))

    def test_add_file(self):
        self._add_file('file.txt')
        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file.txt'})
        with open('file.txt') as f:
            self.assertEqual(f.read(), 'this is some text')

    def test_add_file_to_branch(self):
        self._add_file('file.txt', 'branch')
        check_call_silent(['git', 'checkout', 'branch'])
        assertDirectory('.', {'file.txt'})
        with open('file.txt') as f:
            self.assertEqual(f.read(), 'this is some text')

    def test_delete_files(self):
        self._add_file('file.txt')
        self._add_file('file2.txt')
        with git_utils.Commit('master', 'delete file') as commit:
            commit.delete_files(['file.txt'])

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file2.txt'})

    def test_delete_all_files(self):
        self._add_file('file.txt')
        self._add_file('file2.txt')
        with git_utils.Commit('master', 'delete all files') as commit:
            commit.delete_files('*')

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', set())

    def test_finish(self):
        commit = git_utils.Commit('master', 'add file')
        commit.add_file(git_utils.FileInfo('file.txt', 'this is some text'))
        commit.finish()
        self.assertRaises(git_utils.GitError, commit.finish)
        self.assertRaises(git_utils.GitError, commit.abort)

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file.txt'})

    def test_abort(self):
        self._add_file('file.txt')

        commit = git_utils.Commit('master', 'add file')
        commit.add_file(git_utils.FileInfo('file2.txt', 'this is some text'))
        commit.abort()
        self.assertRaises(git_utils.GitError, commit.finish)
        self.assertRaises(git_utils.GitError, commit.abort)

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file.txt'})

    def test_context_already_finished(self):
        with git_utils.Commit('master', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))
            commit.finish()

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file.txt'})

    def test_handle_exception(self):
        self._add_file('file.txt')
        try:
            with git_utils.Commit('master', 'add file') as commit:
                commit.add_file(git_utils.FileInfo(
                    'file2.txt', 'this is some text'
                ))
                raise ValueError('bad')
        except ValueError:
            pass

        check_call_silent(['git', 'checkout', 'master'])
        assertDirectory('.', {'file.txt'})


class TestPushBranch(unittest.TestCase):
    def setUp(self):
        self.origin = stage_dir('update_branch_origin')
        git_init()
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        commit_file('file.txt', 'initial commit')

        self.stage = stage_dir('update_branch')
        check_call_silent(['git', 'clone', self.origin, '.'])
        git_config()

    def test_push(self):
        commit_file('file2.txt', 'add file2')
        clone_rev = git_utils.get_latest_commit('master')
        git_utils.push_branch('origin', 'master')

        with pushd(self.origin):
            origin_rev = git_utils.get_latest_commit('master')
            self.assertEqual(origin_rev, clone_rev)

    def test_push_fails(self):
        with pushd(self.origin):
            commit_file('file2.txt', 'add file2')

        commit_file('file2.txt', 'add file2 from clone')
        self.assertRaises(git_utils.GitError, git_utils.push_branch, 'origin',
                          'master')

    def test_force_push(self):
        with pushd(self.origin):
            commit_file('file2.txt', 'add file2')

        commit_file('file2.txt', 'add file2 from clone')
        clone_rev = git_utils.get_latest_commit('master')
        git_utils.push_branch('origin', 'master', force=True)

        with pushd(self.origin):
            origin_rev = git_utils.get_latest_commit('master')
            self.assertEqual(origin_rev, clone_rev)


class TestFileMode(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('file_mode')
        os.chdir(self.stage)
        git_init()
        with git_utils.Commit('branch', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'dir/file.txt', 'this is some text'
            ))

    def test_file_mode(self):
        self.assertEqual(git_utils.file_mode('branch', 'dir/file.txt'),
                         0o100644)

    def test_directory_mode(self):
        self.assertEqual(git_utils.file_mode('branch', 'dir'), 0o040000)
        self.assertEqual(git_utils.file_mode('branch', 'dir/'), 0o040000)

    def test_root_mode(self):
        self.assertEqual(git_utils.file_mode('branch', ''), 0o040000)

    def test_nonexistent_file(self):
        self.assertRaises(git_utils.GitError, git_utils.file_mode, 'branch',
                          'nonexist.txt')

    def test_nonexistent_branch(self):
        self.assertRaises(git_utils.GitError, git_utils.file_mode, 'nonexist',
                          'dir/file.txt')


class TestReadFile(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('read_file')
        os.chdir(self.stage)
        git_init()
        with git_utils.Commit('branch', 'add file') as commit:
            commit.add_file(git_utils.FileInfo(
                'file.txt', 'this is some text'
            ))

    def test_read_file(self):
        self.assertEqual(git_utils.read_file('branch', 'file.txt'),
                         b'this is some text')

    def test_read_file_as_text(self):
        self.assertEqual(git_utils.read_file('branch', 'file.txt',
                                             universal_newlines=True),
                         'this is some text')

    def test_nonexistent_file(self):
        self.assertRaises(git_utils.GitError, git_utils.read_file, 'branch',
                          'nonexist.txt')

    def test_nonexistent_branch(self):
        self.assertRaises(git_utils.GitError, git_utils.read_file, 'nonexist',
                          'file.txt')


class TestWalkFiles(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('walk_files')
        os.chdir(self.stage)
        git_init()
        commit_file('file.txt', 'initial commit')

        with git_utils.Commit('branch', 'add file') as commit:
            commit.add_file(git_utils.FileInfo('file.txt', b'text'))
            commit.add_file(git_utils.FileInfo(
                os.path.join('dir/file.txt'), b'more text'
            ))
            commit.add_file(git_utils.FileInfo(
                os.path.join('dir', 'file 2.txt'), b'more text'
            ))
            commit.add_file(git_utils.FileInfo(
                os.path.join('dir', 'subdir', 'file 3.txt'),
                b'even more text'
            ))

    def test_root(self):
        files = sorted(git_utils.walk_files('branch'),
                       key=lambda x: x.path)
        self.assertEqual(files, [
            git_utils.FileInfo(os.path.join('dir', 'file 2.txt'),
                               b'more text'),
            git_utils.FileInfo(os.path.join('dir', 'file.txt'), b'more text'),
            git_utils.FileInfo(os.path.join('dir', 'subdir', 'file 3.txt'),
                               b'even more text'),
            git_utils.FileInfo('file.txt', b'text'),
        ])

    def test_subdir(self):
        files = sorted(git_utils.walk_files('branch', 'dir'),
                       key=lambda x: x.path)
        self.assertEqual(files, [
            git_utils.FileInfo(os.path.join('dir', 'file 2.txt'),
                               b'more text'),
            git_utils.FileInfo(os.path.join('dir', 'file.txt'), b'more text'),
            git_utils.FileInfo(os.path.join('dir', 'subdir', 'file 3.txt'),
                               b'even more text'),
        ])

    def test_nonexistent(self):
        with self.assertRaises(git_utils.GitError):
            list(git_utils.walk_files('branch', 'nonexist'))
        with self.assertRaises(git_utils.GitError):
            list(git_utils.walk_files('nonexist'))


class TestWalkRealFiles(unittest.TestCase):
    mode = 0o100755 if sys.platform == 'win32' else 0o100644

    def setUp(self):
        self.directory = os.path.join(test_data_dir, 'directory')

    def test_walk(self):
        files = sorted(git_utils.walk_real_files(self.directory),
                       key=lambda x: x.path)
        self.assertEqual(files, [
            git_utils.FileInfo(os.path.join(self.directory, 'file.txt'),
                               b'hello there\n', self.mode),
        ])
