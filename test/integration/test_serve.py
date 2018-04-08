from __future__ import unicode_literals

import os
import platform
import signal
import subprocess
import time
import unittest

from .. import *
from mike import git_utils, versions


class TestList(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('serve')
        git_init()
        commit = git_utils.Commit('gh-pages', 'add file')
        commit.add_file(git_utils.FileInfo(
            'index.html', 'main page'
        ))
        commit.add_file(git_utils.FileInfo(
            'dir/index.html', 'sub page'
        ))
        commit.finish()

    @unittest.skipIf(platform.system() == 'Windows',
                     "SIGINT doesn't work on windows")
    def test_serve(self):
        proc = subprocess.Popen(
            ['mike', 'serve', '--dev-addr=localhost:8888'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        time.sleep(1)
        proc.send_signal(signal.SIGINT)
        output = proc.communicate()[0]

        self.assertEqual(proc.returncode, 0)
        self.assertEqual(output,
                         'Starting server at http://localhost:8888/\n' +
                         'Press Ctrl+C to quit.\n' +
                         'Stopping server...\n')
