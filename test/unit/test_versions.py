import json
import unittest
from verspec.loose import LooseVersion as Version

from mike.versions import VersionInfo, Versions


class TestVersionInfo(unittest.TestCase):
    def test_create(self):
        v = VersionInfo('1.0')
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, set())

        v = VersionInfo('1.0', '1.0.0')
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0.0')
        self.assertEqual(v.aliases, set())

        v = VersionInfo('1.0', aliases=['latest'])
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, {'latest'})

        v = VersionInfo(Version('1.0'))
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, set())

        with self.assertRaisesRegex(ValueError, "^'' is not a valid version$"):
            VersionInfo('')
        with self.assertRaisesRegex(ValueError,
                                    "^'..' is not a valid version$"):
            VersionInfo('..')
        with self.assertRaisesRegex(ValueError,
                                    "^'foo/bar' is not a valid version$"):
            VersionInfo('foo/bar')
        with self.assertRaisesRegex(ValueError,
                                    "^'foo/bar' is not a valid version$"):
            VersionInfo(Version('foo/bar'))

        with self.assertRaisesRegex(ValueError, "^'' is not a valid alias$"):
            VersionInfo('1.0', aliases=['latest', ''])
        with self.assertRaisesRegex(ValueError, "^'..' is not a valid alias$"):
            VersionInfo('1.0', aliases=['..'])
        with self.assertRaisesRegex(ValueError,
                                    "^'foo/bar' is not a valid alias$"):
            VersionInfo('1.0', aliases=['foo/bar'])
        with self.assertRaisesRegex(ValueError,
                                    "^duplicated version and alias$"):
            VersionInfo('1.0', aliases=['1.0'])

    def test_equality(self):
        v = VersionInfo('1.0')
        self.assertEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertNotEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', aliases=['latest']))

        v = VersionInfo('1.0', '1.0.0')
        self.assertNotEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', aliases=['latest']))

        v = VersionInfo('1.0', aliases=['latest'])
        self.assertNotEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertNotEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertEqual(v, VersionInfo('1.0', aliases=['latest']))

    def test_dumps(self):
        v = VersionInfo('1.0')
        self.assertEqual(json.loads(v.dumps()), {
            'version': '1.0', 'title': '1.0', 'aliases': []
        })

        v = VersionInfo('1.0', '1.0.0', ['latest'])
        self.assertEqual(json.loads(v.dumps()), {
            'version': '1.0', 'title': '1.0.0', 'aliases': ['latest']
        })

    def test_update(self):
        v = VersionInfo('1.0')
        v.update()
        self.assertEqual(v, VersionInfo('1.0'))

        v.update('1.0.0')
        self.assertEqual(v, VersionInfo('1.0', '1.0.0'))

        v.update('1.0.1', ['latest'])
        self.assertEqual(v, VersionInfo('1.0', '1.0.1', ['latest']))

        v.update(aliases=['greatest'])
        self.assertEqual(v, VersionInfo(
            '1.0', '1.0.1', ['latest', 'greatest']
        ))

        with self.assertRaisesRegex(ValueError, "^'' is not a valid alias$"):
            v.update(aliases=[''])
        with self.assertRaisesRegex(ValueError, "^'..' is not a valid alias$"):
            v.update(aliases=['..'])
        with self.assertRaisesRegex(ValueError,
                                    "^'foo/bar' is not a valid alias$"):
            v.update(aliases=['foo/bar'])


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

    def test_add_overwrite_duplicate_alias(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        v = versions.add('1.0', '1.0.1', ['latest', 'greatest'])
        self.assertEqual(v, VersionInfo('1.0', '1.0.1',
                                        {'latest', 'greatest'}))
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.1', {'latest', 'greatest'}),
        ])

    def test_add_update_alias(self):
        versions = Versions()
        versions.add('1.0', aliases=['latest'])
        v = versions.add('2.0', aliases=['latest'], update_aliases=True)
        self.assertEqual(v, VersionInfo('2.0', aliases={'latest'}))
        self.assertEqual(list(versions), [
            VersionInfo('2.0', aliases={'latest'}),
            VersionInfo('1.0'),
        ])

    def test_add_overwrite_alias(self):
        versions = Versions()
        versions.add('1.0', aliases=['latest'])
        msg = r"alias 'latest' already exists for version '1\.0'"
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('2.0', aliases=['latest'])

    def test_add_overwrite_version_with_alias(self):
        versions = Versions()
        versions.add('1.0b1')

        msg = r"alias '1\.0b1' already specified as a version"
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('1.0', aliases=['1.0b1'])
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('1.0', aliases=['1.0b1'], update_aliases=True)

    def test_add_overwrite_alias_with_version(self):
        versions = Versions()
        versions.add('1.0b1', aliases=['1.0'])
        msg = r"version '1\.0' already exists"
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('1.0')
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('1.0', update_aliases=True)

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

    def test_update_overwrite_same_alias(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        diff = versions.update('1.0', aliases=['latest'])
        self.assertEqual(diff, set())
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0.0', ['latest']),
        ])

    def test_update_overwrite_alias_error(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        versions.add('2.0', '2.0.0')

        msg = r"alias 'latest' already exists for version '1\.0'"
        with self.assertRaisesRegex(ValueError, msg):
            versions.update('2.0', aliases=['latest'])

    def test_update_overwrite_alias_update(self):
        versions = Versions()
        versions.add('1.0', '1.0.0', ['latest'])
        versions.add('2.0', '2.0.0')
        diff = versions.update('2.0', aliases=['latest'], update_aliases=True)
        self.assertEqual(diff, {'latest'})
        self.assertEqual(list(versions), [
            VersionInfo('2.0', '2.0.0', ['latest']),
            VersionInfo('1.0', '1.0.0'),
        ])

    def test_update_invalid_version(self):
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
