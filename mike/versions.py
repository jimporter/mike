from __future__ import unicode_literals

import json
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

    def __repr__(self):
        return '<VersionInfo({!r}, {!r}, {{{}}})>'.format(
            self.version, self.title, ', '.join(repr(i) for i in self.aliases)
        )

    def update(self, title=None, aliases=[]):
        if title is not None:
            self.title = title

        aliases = set(aliases)
        added = aliases - self.aliases
        self.aliases |= aliases
        return added


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

    def add(self, version, title=None, aliases=[]):
        v = _ensure_version(version)
        for i in aliases:
            key = self.find(i)
            if key and key[0] != v:
                raise ValueError("'{}' already exists".format(i))

        if v in self._data:
            self._data[v].update(title, aliases)
        else:
            if self.find(version):
                raise ValueError("'{}' already exists".format(version))
            self._data[v] = VersionInfo(version, title, aliases)

        return self._data[v]

    def update(self, version, title=None, aliases=[]):
        key = self.find(version)
        if key is None:
            raise KeyError(version)

        return self._data[key[0]].update(title, aliases)

    def remove(self, version):
        key = self.find(version)
        if key is None:
            raise KeyError(version)
        elif len(key) == 1:
            item = self._data[key[0]]
            del self._data[key[0]]
        else:
            item = key[1]
            self._data[key[0]].aliases.remove(key[1])
        return item

    def difference_update(self, versions):
        versions = list(versions)
        for i in versions:
            if self.find(i) is None:
                raise KeyError(i)
        return [self.remove(i) for i in versions]
