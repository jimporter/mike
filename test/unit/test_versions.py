from __future__ import unicode_literals

import json
import unittest
from packaging.version import LegacyVersion as Version

from mike.versions import VersionInfo, Versions


class TestVersions(unittest.TestCase):
    def test_add(self):
        versions = Versions()
        v = versions.add('1.0')
        self.assertEqual(v, VersionInfo('1.0'))
        self.assertEqual(list(versions), [
            VersionInfo('1.0'),
        ])

    def test_add_title(self):
        versions = Versions()
        v = versions.add('1.0', '1.0.0')
        self.assertEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.0'),
        ])

    def test_add_aliases(self):
        versions = Versions()
        v = versions.add('1.0', aliases=['latest'])
        self.assertEqual(v, VersionInfo('1.0', aliases={'latest'}))
        self.assertEqual(list(versions), [
            VersionInfo('1.0', aliases={'latest'}),
        ])

    def test_add_overwrite(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        v = versions.add('1.0', '1.0.1', ['greatest'])
        self.assertEqual(v, VersionInfo('1.0', '1.0.1',
                                        {'latest', 'greatest'}))
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.1', {'latest', 'greatest'}),
        ])

    def test_add_overwrite_alias(self):
        versions = Versions()
        versions.add('1.0', aliases=['latest'])
        with self.assertRaises(ValueError):
            versions.add('2.0', aliases=['latest'])

    def test_add_overwrite_version_with_alias(self):
        versions = Versions()
        versions.add('1.0b1')
        with self.assertRaises(ValueError):
            versions.add('1.0', aliases=['1.0b1'])

    def test_add_overwrite_alias_with_version(self):
        versions = Versions()
        versions.add('1.0b1', aliases=['1.0'])
        with self.assertRaises(ValueError):
            versions.add('1.0')

    def test_add_invalid(self):
        versions = Versions()
        with self.assertRaises(ValueError):
            versions.add('1.0', aliases=['1.0'])

    def test_update_version_title(self):
        versions = Versions()
        versions.add('1.0', '1.0.0')
        diff = versions.update('1.0', '1.0.1')
        self.assertEqual(diff, set())
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.1'),
        ])

    def test_update_alias_title(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        diff = versions.update('latest', '1.0.1')
        self.assertEqual(diff, set())
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.1', ['latest']),
        ])

    def test_update_version_aliases(self):
        versions = Versions()
        versions.add('1.0', '1.0.0')
        diff = versions.update('1.0', aliases=['latest'])
        self.assertEqual(diff, {'latest'})
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.0', ['latest']),
        ])

    def test_update_alias_aliases(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        diff = versions.update('latest', aliases=['greatest'])
        self.assertEqual(diff, {'greatest'})
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.0', ['latest', 'greatest']),
        ])

    def test_update_invalid(self):
        versions = Versions()
        with self.assertRaises(KeyError):
            versions.update('1.0', '1.0.0')

    def test_len(self):
        versions = Versions()
        versions.add('1.0')
        versions.add('1.0')
        versions.add('2.0')
        self.assertEqual(len(versions), 2)

    def test_getitem(self):
        versions = Versions()
        versions.add('1.0')
        self.assertEqual(versions['1.0'], VersionInfo('1.0'))
        self.assertEqual(versions[Version('1.0')], VersionInfo('1.0'))

    def test_remove_version(self):
        versions = Versions()
        versions.add('1.0')
        v = versions.remove('1.0')
        self.assertEqual(v, VersionInfo('1.0'))
        self.assertEqual(list(versions), [])

    def test_remove_alias(self):
        versions = Versions()
        versions.add('1.0', aliases=['latest'])
        v = versions.remove('latest')
        self.assertEqual(v, 'latest')
        self.assertEqual(list(versions), [
            VersionInfo('1.0'),
        ])

    def test_remove_nonexistent(self):
        versions = Versions()
        with self.assertRaises(KeyError):
            versions.remove('1.0')

    def test_difference_update(self):
        versions = Versions()
        versions.add('1.0')
        versions.add('2.0')
        versions.add('3.0', aliases=['latest'])
        v = versions.difference_update(['1.0', '2.0', 'latest'])
        self.assertEqual(v, [VersionInfo('1.0'), VersionInfo('2.0'), 'latest'])
        self.assertEqual(list(versions), [
            VersionInfo('3.0'),
        ])

    def test_difference_update_nonexistent(self):
        versions = Versions()
        versions.add('1.0')
        versions.add('2.0')
        versions.add('3.0', aliases=['latest'])

        with self.assertRaises(KeyError):
            versions.difference_update(['1.0', 'latest', '4.0'])
        self.assertEqual(list(versions), [
            VersionInfo('3.0', aliases=['latest']),
            VersionInfo('2.0'),
            VersionInfo('1.0'),
        ])

    def test_loads(self):
        versions = Versions.loads(
            '[' +
            '{"version": "2.0", "title": "2.0.2", "aliases": ["latest"]}, ' +
            '{"version": "1.0", "title": "1.0.1", "aliases": ["stable"]}' +
            ']'
        )
        self.assertEqual(list(versions), [
            VersionInfo('2.0', '2.0.2', aliases={'latest'}),
            VersionInfo('1.0', '1.0.1', aliases={'stable'}),
        ])

    def test_dumps(self):
        versions = Versions()
        versions.add('2.0', '2.0.2', ['latest'])
        versions.add('1.0', '1.0.1', ['stable'])
        self.assertEqual(json.loads(versions.dumps()), [
            {'version': '2.0', 'title': '2.0.2', 'aliases': ['latest']},
            {'version': '1.0', 'title': '1.0.1', 'aliases': ['stable']}
        ])
