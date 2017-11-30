from __future__ import unicode_literals

import os
import subprocess
import unittest
from itertools import chain
from six import assertRegex

from . import assertPopen
from .. import *
from mkultra import versions


class TestDeploy(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('deploy')
        git_init()
        copytree(os.path.join(test_data_dir, 'mkdocs'), self.stage)
        check_call_silent(['git', 'add', 'mkdocs.yml', 'docs'])
        check_call_silent(['git', 'commit', '-m', 'initial commit'])

    def _test_deploy(self, expected_message=None,
                     version=versions.VersionInfo('1.0')):
        message = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'],
                                          universal_newlines=True).rstrip()
        if expected_message:
            self.assertEqual(message, expected_message)
        else:
            assertRegex(
                self, message,
                r'^Deployed \S+ to 1.0 with MkDocs \S+ and mkultra \S+$'
            )

        dirs = {str(version.version)} | version.aliases
        contents = {'versions.json'} | set(chain.from_iterable(
            (d, d + '/index.html') for d in dirs
        ))
        assertDirectory('.', contents, allow_extra=True)

        with open('versions.json') as f:
            self.assertEqual(list(versions.Versions.loads(f.read())), [
                version,
            ])

    def test_default(self):
        assertPopen(['mkultra', 'deploy', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy()

    def test_title(self):
        assertPopen(['mkultra', 'deploy', '-t', '1.0.0', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(version=versions.VersionInfo('1.0', '1.0.0'))

    def test_aliases(self):
        assertPopen(['mkultra', 'deploy', '1.0', 'latest'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy(version=versions.VersionInfo(
            '1.0', aliases=['latest']
        ))

    def test_branch(self):
        assertPopen(['mkultra', 'deploy', '-b', 'branch', '1.0'])
        check_call_silent(['git', 'checkout', 'branch'])
        self._test_deploy()

    def test_commit_message(self):
        assertPopen(['mkultra', 'deploy', '-m', 'commit message', '1.0'])
        check_call_silent(['git', 'checkout', 'gh-pages'])
        self._test_deploy('commit message')

    def test_push(self):
        check_call_silent(['git', 'config', 'receive.denyCurrentBranch',
                           'ignore'])
        clone = stage_dir('deploy_clone')
        check_call_silent(['git', 'clone', self.stage, '.'])
        git_config()

        assertPopen(['mkultra', 'deploy', '-p', '1.0'])
