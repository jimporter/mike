from __future__ import unicode_literals

import json
from itertools import chain
from packaging.version import LegacyVersion as Version
from six import iteritems


def _ensure_version(version):
    if not isinstance(version, Version):
        return Version(version)
    return version


def _version_pair(version):
    return _ensure_version(version), str(version)


class VersionInfo(object):
    def __init__(self, version, title=None, aliases=[]):
        self.version, name = _version_pair(version)
        self.title = name if title is None else title
        self.aliases = set(aliases)

        if name in self.aliases:
            raise ValueError('duplicated version and alias')

    def __eq__(self, rhs):
        return (self.version == rhs.version and self.title == rhs.title and
                self.aliases == rhs.aliases)


class Versions(object):
    def __init__(self):
        self._data = {}

    @staticmethod
    def loads(data):
        result = Versions()
        for i in json.loads(data):
            result.add(i['version'], i['title'], i['aliases'])
        return result

    def dumps(self):
        return json.dumps([{
            'version': str(i.version),
            'title': i.title,
            'aliases': list(i.aliases),
        } for i in iter(self)])

    def __iter__(self):
        return (i for _, i in sorted(iteritems(self._data), reverse=True))

    def __len__(self):
        return len(self._data)

    def __getitem__(self, k):
        return self._data[_ensure_version(k)]

    def find(self, version):
        version, name = _version_pair(version)
        if version in self._data:
            return (version,)
        for k, v in iteritems(self._data):
            if name in v.aliases:
                return (k, name)
        return None

    def add(self, version, title=None, aliases=[], strict=False):
        info = VersionInfo(version, title, aliases)

        if info.version in self._data:
            old = self._data[info.version].aliases
            added = info.aliases - old
            removed = old - info.aliases
        else:
            added = set(chain(info.aliases, [str(info.version)]))
            removed = set()

        if removed and strict:
            raise ValueError('orphaned aliases')
        for i in added:
            key = self.find(i)
            if key:
                if strict:
                    raise ValueError('overwriting version')
                self._remove(key)

        self._data[info.version] = info

    def _remove(self, key):
        if len(key) == 1:
            del self._data[key[0]]
        else:
            self._data[key[0]].aliases.remove(key[1])

    def remove(self, version):
        key = self.find(version)
        if key is None:
            raise KeyError(version)
        self._remove(key)

    def difference_update(self, versions):
        for i in versions:
            self.remove(i)

    def rename(self, version, title):
        key = self.find(version)
        if key is None:
            raise KeyError(version)
        self._data[key[0]].title = title
