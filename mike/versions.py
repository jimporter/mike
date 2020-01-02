import json
from packaging.version import LegacyVersion as Version


def _ensure_version(version):
    if not isinstance(version, Version):
        return Version(version)
    return version


def _version_pair(version):
    return _ensure_version(version), str(version)


class VersionInfo:
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

    def to_json(self):
        return {'version': str(self.version),
                'title': self.title,
                'aliases': list(self.aliases)}

    def dumps(self):
        return json.dumps(self.to_json())

    def update(self, title=None, aliases=[]):
        if title is not None:
            self.title = title

        aliases = set(aliases)
        added = aliases - self.aliases
        self.aliases |= aliases
        return added


class Versions:
    def __init__(self):
        self._data = {}

    @staticmethod
    def loads(data):
        result = Versions()
        for i in json.loads(data):
            result.add(i['version'], i['title'], i['aliases'])
        return result

    def dumps(self):
        return json.dumps([i.to_json() for i in iter(self)])

    def __iter__(self):
        return (i for _, i in sorted(self._data.items(), reverse=True))

    def __len__(self):
        return len(self._data)

    def __getitem__(self, k):
        return self._data[_ensure_version(k)]

    def find(self, version, strict=False):
        version, name = _version_pair(version)
        if version in self._data:
            return (version,)
        for k, v in self._data.items():
            if name in v.aliases:
                return (k, name)
        if strict:
            raise KeyError(version)
        return None

    def add(self, version, title=None, aliases=[], update_aliases=False):
        v = _ensure_version(version)
        removed_aliases = []
        for i in aliases:
            key = self.find(i)
            if key and key[0] != v:
                if not update_aliases or len(key) == 1:
                    raise ValueError('{!r} already exists'.format(i))
                removed_aliases.append(key)

        if v in self._data:
            self._data[v].update(title, aliases)
        else:
            if self.find(version):
                raise ValueError('{!r} already exists'.format(version))
            self._data[v] = VersionInfo(version, title, aliases)

        for i in removed_aliases:
            self._data[i[0]].aliases.remove(i[1])

        return self._data[v]

    def update(self, version, title=None, aliases=[]):
        key = self.find(version, strict=True)
        return self._data[key[0]].update(title, aliases)

    def _remove_by_key(self, key):
        if len(key) == 1:
            item = self._data[key[0]]
            del self._data[key[0]]
        else:
            item = key[1]
            self._data[key[0]].aliases.remove(key[1])
        return item

    def remove(self, version):
        key = self.find(version, strict=True)
        return self._remove_by_key(key)

    def difference_update(self, versions):
        keys = [self.find(i, strict=True) for i in versions]
        return [self._remove_by_key(i) for i in keys]
