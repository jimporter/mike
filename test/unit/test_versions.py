from __future__ import unicode_literals

import json
import unittest
from packaging.version import LegacyVersion as Version

from mkultra.versions import VersionInfo, Versions


class TestVersions(unittest.TestCase):
    def test_add(self):
        v = Versions()
        v.add('1.0')
        self.assertEqual(list(v), [
            VersionInfo('1.0'),
        ])

    def test_add_title(self):
        v = Versions()
        v.add('1.0', '1.0.0')
        self.assertEqual(list(v), [
            VersionInfo('1.0', '1.0.0'),
        ])

    def test_add_aliases(self):
        v = Versions()
        v.add('1.0', aliases=['latest'])
        self.assertEqual(list(v), [
            VersionInfo('1.0', aliases={'latest'}),
        ])

    def test_add_overwrite(self):
        v = Versions()
        v.add('1.0', '1.0.0', ['latest'])
        v.add('1.0', '1.0.1', ['greatest'])
        self.assertEqual(list(v), [
            VersionInfo('1.0', '1.0.1', aliases={'greatest'}),
        ])

    def test_add_overwrite_other_alias(self):
        v = Versions()
        v.add('1.0', aliases=['latest'])
        v.add('2.0', aliases=['latest'])
        self.assertEqual(list(v), [
            VersionInfo('2.0', aliases={'latest'}),
            VersionInfo('1.0'),
        ])

    def test_add_overwrite_other_version(self):
        v = Versions()
        v.add('1.0b1')
        v.add('1.0', aliases=['1.0b1'])
        self.assertEqual(list(v), [
            VersionInfo('1.0', aliases={'1.0b1'}),
        ])

    def test_add_strict(self):
        v = Versions()
        v.add('2.0', aliases=['latest'])
        v.add('1.0', aliases=['greatest'])
        v.add('1.0', aliases=['greatest'], strict=True)
        self.assertEqual(list(v), [
            VersionInfo('2.0', aliases={'latest'}),
            VersionInfo('1.0', aliases={'greatest'}),
        ])

        with self.assertRaises(ValueError):
            v.add('1.0', aliases=['latest', 'greatest'], strict=True)
        with self.assertRaises(ValueError):
            v.add('1.0', strict=True)

    def test_add_invalid(self):
        v = Versions()
        with self.assertRaises(ValueError):
            v.add('1.0', aliases=['1.0'])

    def test_len(self):
        v = Versions()
        v.add('1.0')
        v.add('1.0')
        v.add('2.0')
        self.assertEqual(len(v), 2)

    def test_getitem(self):
        v = Versions()
        v.add('1.0')
        self.assertEqual(v['1.0'], VersionInfo('1.0'))
        self.assertEqual(v[Version('1.0')], VersionInfo('1.0'))

    def test_remove_version(self):
        v = Versions()
        v.add('1.0')
        v.remove('1.0')
        self.assertEqual(list(v), [])

    def test_remove_alias(self):
        v = Versions()
        v.add('1.0', aliases=['latest'])
        v.remove('latest')
        self.assertEqual(list(v), [
            VersionInfo('1.0'),
        ])

    def test_remove_nonexistent(self):
        v = Versions()
        with self.assertRaises(KeyError):
            v.remove('1.0')

    def test_difference_update(self):
        v = Versions()
        v.add('1.0')
        v.add('2.0')
        v.add('3.0', aliases=['latest'])
        v.difference_update(['1.0', '2.0', 'latest'])
        self.assertEqual(list(v), [
            VersionInfo('3.0'),
        ])

    def test_loads(self):
        v = Versions.loads(
            '[' +
            '{"version": "2.0", "title": "2.0.2", "aliases": ["latest"]}, ' +
            '{"version": "1.0", "title": "1.0.1", "aliases": ["stable"]}' +
            ']'
        )
        self.assertEqual(list(v), [
            VersionInfo('2.0', '2.0.2', aliases={'latest'}),
            VersionInfo('1.0', '1.0.1', aliases={'stable'}),
        ])

    def test_dumps(self):
        v = Versions()
        v.add('2.0', '2.0.2', ['latest'])
        v.add('1.0', '1.0.1', ['stable'])
        self.assertEqual(json.loads(v.dumps()), [
            {'version': '2.0', 'title': '2.0.2', 'aliases': ['latest']},
            {'version': '1.0', 'title': '1.0.1', 'aliases': ['stable']}
        ])

