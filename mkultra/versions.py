import json
from packaging.version import LegacyVersion as Version
from six import iteritems

from . import git_utils


def _ensure_version(version):
    if not isinstance(version, Version):
        return Version(version)
    return version


class Versions(object):
    versions_file = 'versions.json'

    def __init__(self):
        self._data = {}

    @staticmethod
    def load_from_git(branch, filename=versions_file):
        result = Versions.__new__(Versions)
        try:
            data = json.loads(git_utils.read_file(branch, filename))
            result._data = {Version(i['version']): i['aliases'] for i in data}
        except ValueError:
            result._data = {}
        return result

    def __iter__(self):
        return iter(sorted(iteritems(self._data), reverse=True))

    def add(self, version, aliases=[]):
        self._data[_ensure_version(version)] = aliases

    def remove(self, version):
        del self._data[_ensure_version(version)]

    def difference_update(self, versions):
        for i in versions:
            self.remove(i)

    def to_json(self):
        return json.dumps([{'version': str(v), 'aliases': a}
                           for v, a in iter(self)])

    def to_file_info(self, filename=versions_file):
        return git_utils.FileInfo(filename, self.to_json())
