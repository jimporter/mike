import unittest

from . import assertPopen


class HelpTest(unittest.TestCase):
    def test_help(self):
        output = assertPopen(['mike', 'help'])
        self.assertRegex(
            output, r'^usage: mike \[-h\] \[--version\] COMMAND \.\.\.'
        )

    def test_help_subcommand(self):
        output = assertPopen(['mike', 'help', 'deploy'])
        self.assertRegex(output, r'^usage: mike deploy')

    def test_help_subcommand_extra(self):
        output = assertPopen(['mike', 'help', 'deploy', '--rebase'])
        self.assertRegex(output, r'^usage: mike deploy')


class DumpCompletionTest(unittest.TestCase):
    def test_completion(self):
        output = assertPopen(['mike', 'dump-completion', '-sbash'])
        self.assertRegex(output, r'^#!/usr/bin/env bash')
