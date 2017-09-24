import json
from six import iteritems

from . import git_utils

class Versions(object):
    versions_file = 'versions.json'

    def __init__(self):
        self._data = {}

    @staticmethod
    def load_from_git(branch, filename=versions_file):
        result = Versions.__new__(Versions)
        try:
            data = json.loads(git_utils.read_file(branch, filename))
            result._data = {i['version']: i['aliases'] for i in data}
        except:
            result._data = {}
        return result

    def add(self, version, aliases=[]):
        self._data[version] = aliases

    def remove(self, version):
        del self._data[version]

    def difference_update(self, versions):
        for i in versions:
            self.remove(i)

    def to_json(self):
        return json.dumps(sorted([
            {"version": k, "aliases": v} for k, v in iteritems(self._data)
        ]))

    def to_file_info(self, filename=versions_file):
        return git_utils.FileInfo(filename, self.to_json())


