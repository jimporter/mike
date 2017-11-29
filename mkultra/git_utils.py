# This file is based on the ghp-import package released under
# the Tumbolia Public License.

#                            Tumbolia Public License

# Copyright 2013, Paul Davis <paul.joseph.davis@gmail.com>

# Copying and distribution of this file, with or without modification, are
# permitted in any medium without royalty provided the copyright notice and
# this notice are preserved.

# TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

#   0. opan saurce LOL

from __future__ import division, unicode_literals

import os
import subprocess as sp
import sys
import time
import unicodedata

from six import binary_type, text_type


def git_path(path):
    path = os.path.normpath(path)
    # Fix unicode pathnames on macOS; see
    # <http://stackoverflow.com/a/5582439/44289>.
    if sys.platform == 'darwin':  # pragma: no cover
        if isinstance(path, binary_type):
            path = path.decode('utf-8')
        path = unicodedata.normalize('NFKC', path)
    return '/'.join(path.split(os.path.sep))


def make_when(timestamp=None):
    if timestamp is None:
        timestamp = int(time.time())
    timezone = '{:+05d}'.format(-1 * time.timezone // 3600 * 100)
    return '{} {}'.format(timestamp, timezone)


def get_config(key):
    cmd = ['git', 'config', key]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    if p.wait() != 0:
        raise ValueError('Error getting config: {}'.format(stderr))
    return stdout.strip()


def get_latest_commit(rev):
    cmd = ['git', 'rev-list', '--max-count=1', rev, '--']
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    if p.wait() != 0:
        raise ValueError('Error getting latest commit: {}'.format(stderr))
    return stdout.strip()


def update_branch(remote, branch):
    try:
        rev = get_latest_commit('{}/{}'.format(remote, branch))
        cmd = ['git', 'update-ref', 'refs/heads/{}'.format(branch), rev]
        if sp.call(cmd) != 0:  # pragma: no cover
            raise ValueError('Failed to update branch')
    except ValueError:
        # Couldn't get any commits, so there's probably no branch (which is
        # fine).
        pass


class FileInfo(object):
    def __init__(self, path, data, mode='100644'):
        self.path = path
        self.mode = mode
        self.data = data

    def __eq__(self, rhs):
        return (self.path == rhs.path and self.mode == rhs.mode and
                self.data == rhs.data)

    def __repr__(self):
        return '<FileInfo({!r})>'.format(self.path)


class Commit(object):
    def __init__(self, branch, message):
        cmd = ['git', 'fast-import', '--date-format=raw', '--quiet']
        self._pipe = sp.Popen(cmd, stdin=sp.PIPE, universal_newlines=False)
        self._start_commit(branch, message)

    def _write(self, data):
        if isinstance(data, text_type):  # pragma: no branch
            data = data.encode('utf-8')
        return self._pipe.stdin.write(data)

    def _start_commit(self, branch, message):
        name = get_config('user.name')
        email = get_config('user.email')
        self._write('commit refs/heads/{}\n'.format(branch))
        self._write('committer {name} <{email}> {time}\n'.format(
            name=name, email=email, time=make_when()
        ))
        self._write('data {length}\n{message}\n'.format(
            length=len(message), message=message
        ))
        try:
            head = get_latest_commit(branch)
            self._write('from {}\n'.format(head))
        except ValueError:
            pass

    def delete_files(self, files):
        if files == '*':
            self._write('deleteall\n')
        else:
            for f in files:
                self._write('D {}\n'.format(f))

    def add_file(self, file_info):
        self._write('M {mode} inline {path}\n'.format(
            path=git_path(file_info.path), mode=file_info.mode
        ))
        self._write('data {}\n'.format(len(file_info.data)))
        self._write(file_info.data)
        self._write('\n')

    def finish(self):
        self._write('\n')
        self._pipe.stdin.close()
        if self._pipe.wait() != 0:  # pragma: no cover
            raise ValueError('Failed to process commit')


def push_branch(remote, branch, force=False):
    cmd = ['git', 'push'] + (['--force'] if force else []) + [remote, branch]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    if p.wait() != 0:
        raise ValueError('Failed to push branch: {}'.format(stderr))


def walk_files(srcdir, dstdirs=['']):
    for path, _, filenames in os.walk(srcdir):
        for f in filenames:
            inpath = os.path.join(path, f)
            with open(inpath, 'rb') as fd:
                mode = '100755' if os.access(inpath, os.X_OK) else '100644'
                data = fd.read()
            for d in dstdirs:
                outpath = os.path.join(
                    d, os.path.relpath(inpath, start=srcdir)
                )
                yield FileInfo(outpath, data, mode)


def read_file(branch, filename, universal_newlines=False):
    cmd = ['git', 'show', '{branch}:{filename}'.format(
        branch=branch, filename=filename
    )]
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE,
                 universal_newlines=universal_newlines)
    stdout, stderr = p.communicate()
    if p.wait() != 0:
        raise ValueError('Unable to read file: {}'.format(stderr))
    return stdout
