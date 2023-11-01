import subprocess
import unittest


class SubprocessError(unittest.TestCase.failureException):
    def __init__(self, stdout, stderr=None):
        line = '-' * 60
        if stderr:
            output = 'stdout:\n{stdout}\n{line}stderr:\n{stderr}'.format(
                line=line, stdout=stdout, stderr=stderr
            )
        else:
            output = stdout

        super().__init__('\n{line}\n{output}\n{line}'.format(
            line=line, output=output
        ))


def assertPopen(command, returncode=0, stderr=False):
    proc = subprocess.run(
        command, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if stderr else subprocess.STDOUT,
        universal_newlines=True
    )
    if proc.returncode != returncode:
        raise SubprocessError(proc.stdout, proc.stderr)
    if stderr:
        return proc.stdout, proc.stderr
    return proc.stdout


def assertOutput(test, command, stdout, stderr=None, *args, **kwargs):
    result = assertPopen(command, stderr=stderr is not None, *args, **kwargs)
    if stderr is not None:
        test.assertEqual(result[0], stdout)
        test.assertEqual(result[1], stderr)
    else:
        test.assertEqual(result, stdout)
    return result
