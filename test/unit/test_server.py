from __future__ import unicode_literals

import os
import re
import subprocess
import sys
import unittest
from six import assertRegex

from .. import *
from .mock_server import MockRequest, MockServer
from mike import git_utils
from mike import server


class TestGitBranchHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.stage = stage_dir('server')
        git_init()
        commit = git_utils.Commit('branch', 'add file')
        commit.add_file(git_utils.FileInfo(
            'index.html', 'main page'
        ))
        commit.add_file(git_utils.FileInfo(
            'dir/index.html', 'sub page'
        ))
        commit.finish()

        class Handler(server.GitBranchHTTPHandler):
            branch = 'branch'

            # Use a buffered response in Python 3.6+, since it's easier for
            # testing.
            if sys.version_info >= (3, 6):
                wbufsize = -1

            def log_message(self, *args):
                pass

        self.server = MockServer(('0.0.0.0', 8888), Handler)

    def test_root(self):
        req = MockRequest()
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'main page$'
        )

    def test_file(self):
        req = MockRequest(path=b'/index.html')
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'main page$'
        )

    def test_dir(self):
        req = MockRequest(path=b'/dir/')
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n' +
            b'sub page$'
        )

    def test_dir_redirect(self):
        req = MockRequest(path=b'/dir')
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 301 Moved Permanently\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Location: /dir/\r\n\r\n$'
        )

    def test_head(self):
        req = MockRequest(b'HEAD', b'/index.html')
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 200 OK\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n' +
            b'Content-Type: text/html\r\n\r\n$'
        )

    def test_404(self):
        req = MockRequest(path=b'/nonexist')
        self.server.handle_request(req)
        assertRegex(
            self, req.response,
            b'HTTP/1.0 404 File not found\r\n' +
            b'Server: MikeHTTP.*\r\n' +
            b'Date: .*\r\n'
        )
