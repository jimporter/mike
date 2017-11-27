import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from itertools import chain

__all__ = ['this_dir', 'test_data_dir', 'test_stage_dir', 'stage_dir', 'pushd',
           'check_call_silent', 'assertDirectory']

this_dir = os.path.abspath(os.path.dirname(__file__))
test_data_dir = os.path.join(this_dir, 'data')
test_stage_dir = os.path.join(this_dir, 'stage')

# Clear the stage directory for this test run.
if os.path.exists(test_stage_dir):
    shutil.rmtree(test_stage_dir)
os.makedirs(test_stage_dir)

def stage_dir(name):
    stage = tempfile.mkdtemp(prefix=name + '-', dir=test_stage_dir)
    os.chdir(stage)
    return stage


@contextmanager
def pushd(dirname):
    old = os.getcwd()
    os.chdir(dirname)
    yield
    os.chdir(old)


def check_call_silent(args):
    subprocess.check_output(args, stderr=subprocess.STDOUT)


def remove_in_place(x, func):
    for i in reversed(range(len(x))):
        if func(x[i]):
            del x[i]


def walk(top, include_hidden):
    for base, dirs, files in os.walk(top):
        if not include_hidden:
            remove_in_place(dirs, lambda x: x[0] == '.')
            remove_in_place(files, lambda x: x[0] == '.')
        yield base, dirs, files


def assertDirectory(path, contents, include_hidden=False):
    path = os.path.normpath(path)
    actual = set(os.path.normpath(os.path.join(path, base, f))
                 for base, dirs, files in walk(path, include_hidden)
                 for f in chain(files, dirs))
    expected = set(os.path.normpath(os.path.join(path, i)) for i in contents)
    if actual != expected:
        missing = [os.path.relpath(i, path) for i in (expected - actual)]
        extra = [os.path.relpath(i, path) for i in (actual - expected)]
        raise unittest.TestCase.failureException(
            'missing: {}, extra: {}'.format(missing, extra)
        )
