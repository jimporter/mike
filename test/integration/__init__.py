import subprocess
import unittest


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, message):
        unittest.TestCase.failureException.__init__(
            self, '\n{line}\n{msg}\n{line}'.format(line='-' * 60, msg=message)
        )


def assertPopen(command, returncode=0):
    proc = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    if proc.returncode != returncode:
        raise SubprocessError(proc.stdout)
    return proc.stdout


def assertOutput(test, command, output, *args, **kwargs):
    test.assertEqual(assertPopen(command, *args, **kwargs), output)
