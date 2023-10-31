import json
import unittest
from verspec.loose import LooseVersion as Version

from mike.jsonpath import Deleted
from mike.versions import VersionInfo, Versions


class TestVersionInfo(unittest.TestCase):
    def test_create(self):
        v = VersionInfo('1.0')
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, set())
        self.assertEqual(v.properties, None)

        v = VersionInfo('1.0', '1.0.0')
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0.0')
        self.assertEqual(v.aliases, set())
        self.assertEqual(v.properties, None)

        v = VersionInfo('1.0', aliases=['latest'])
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, {'latest'})
        self.assertEqual(v.properties, None)

        v = VersionInfo('1.0', properties={'prop': 'val'})
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, set())
        self.assertEqual(v.properties, {'prop': 'val'})

        v = VersionInfo(Version('1.0'))
        self.assertEqual(v.version, Version('1.0'))
        self.assertEqual(v.title, '1.0')
        self.assertEqual(v.aliases, set())
        self.assertEqual(v.properties, None)

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
                                    '^duplicated version and alias$'):
            VersionInfo('1.0', aliases=['1.0'])

    def test_equality(self):
        v = VersionInfo('1.0')
        self.assertEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertNotEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', aliases=['latest']))
        self.assertNotEqual(v, VersionInfo('1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0.0', '1.0'))
        self.assertNotEqual(v, VersionInfo('1.0', properties={'prop': 'val'}))

        v = VersionInfo('1.0', '1.0.0')
        self.assertNotEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', aliases=['latest']))
        self.assertNotEqual(v, VersionInfo('1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', properties={'prop': 'val'}))

        v = VersionInfo('1.0', aliases=['latest'])
        self.assertNotEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertNotEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertEqual(v, VersionInfo('1.0', aliases=['latest']))
        self.assertNotEqual(v, VersionInfo('1.0', properties={'prop': 'val'}))

        v = VersionInfo('1.0', properties={'prop': 'val'})
        self.assertNotEqual(v, VersionInfo('1.0'))
        self.assertNotEqual(v, VersionInfo('1.1'))
        self.assertNotEqual(v, VersionInfo('1.0', '1.0.0'))
        self.assertNotEqual(v, VersionInfo('1.0', aliases=['latest']))
        self.assertEqual(v, VersionInfo('1.0', properties={'prop': 'val'}))

    def test_from_json(self):
        self.assertEqual(VersionInfo.from_json({
            'version': '1.0', 'title': '1.0', 'aliases': []
        }), VersionInfo('1.0'))

        self.assertEqual(VersionInfo.from_json({
            'version': '1.0', 'title': '1.0.0', 'aliases': ['latest']
        }), VersionInfo('1.0', '1.0.0', ['latest']))

        self.assertEqual(VersionInfo.from_json({
            'version': '1.0', 'title': '1.0.0', 'aliases': [],
            'properties': {'prop': 'val'}
        }), VersionInfo('1.0', '1.0.0', [], {'prop': 'val'}))

    def test_to_json(self):
        v = VersionInfo('1.0')
        self.assertEqual(v.to_json(), {
            'version': '1.0', 'title': '1.0', 'aliases': []
        })

        v = VersionInfo('1.0', '1.0.0', ['latest'])
        self.assertEqual(v.to_json(), {
            'version': '1.0', 'title': '1.0.0', 'aliases': ['latest']
        })

        v = VersionInfo('1.0', '1.0.0', [], {'prop': 'val'})
        self.assertEqual(v.to_json(), {
            'version': '1.0', 'title': '1.0.0', 'aliases': [],
            'properties': {'prop': 'val'}
        })

    def test_loads(self):
        self.assertEqual(VersionInfo.loads(
            '{"version": "1.0", "title": "1.0", "aliases": []}'
        ), VersionInfo('1.0'))

    def test_dumps(self):
        v = VersionInfo('1.0')
        self.assertEqual(json.loads(v.dumps()), {
            'version': '1.0', 'title': '1.0', 'aliases': []
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

    def test_get_property(self):
        v = VersionInfo('1.0', properties={'prop': 'val'})
        self.assertEqual(v.get_property('prop'), 'val')

        v = VersionInfo('1.0', properties={'prop': ['foo', 'bar']})
        self.assertEqual(v.get_property('prop[1]'), 'bar')

    def test_set_property(self):
        v = VersionInfo('1.0', properties={'prop': 'val'})
        v.set_property('hello', 'world')
        self.assertEqual(v.properties, {'prop': 'val', 'hello': 'world'})

        v = VersionInfo('1.0', properties={'prop': ['foo', 'bar']})
        v.set_property('prop[1]', Deleted)
        self.assertEqual(v.properties, {'prop': ['foo']})


class TestVersions(unittest.TestCase):
    def test_add(self):
        versions = Versions()
        v = versions.add('1.0')
        self.assertEqual(v, VersionInfo('1.0'))
        self.assertEqual(list(versions), [
            VersionInfo('1.0'),
        ])

        v = versions.add('2.0')
        self.assertEqual(v, VersionInfo('2.0'))
        self.assertEqual(list(versions), [
            VersionInfo('2.0'),
            VersionInfo('1.0'),
        ])

        v = versions.add('0.2')
        self.assertEqual(v, VersionInfo('0.2'))
        self.assertEqual(list(versions), [
            VersionInfo('2.0'),
            VersionInfo('1.0'),
            VersionInfo('0.2'),
        ])

        v = versions.add('0.10')
        self.assertEqual(v, VersionInfo('0.10'))
        self.assertEqual(list(versions), [
            VersionInfo('2.0'),
            VersionInfo('1.0'),
            VersionInfo('0.10'),
            VersionInfo('0.2'),
        ])

        v = versions.add('post')
        self.assertEqual(v, VersionInfo('post'))
        self.assertEqual(list(versions), [
            VersionInfo('post'),
            VersionInfo('2.0'),
            VersionInfo('1.0'),
            VersionInfo('0.10'),
            VersionInfo('0.2'),
        ])

        v = versions.add('pre')
        self.assertEqual(v, VersionInfo('pre'))
        self.assertEqual(list(versions), [
            VersionInfo('post'),
            VersionInfo('pre'),
            VersionInfo('2.0'),
            VersionInfo('1.0'),
            VersionInfo('0.10'),
            VersionInfo('0.2'),
        ])

    def test_sort_development_versions(self):
        versions = Versions()
        versions.add('alpha')
        versions.add('beta')
        versions.add('pre')
        versions.add('post')
        versions.add('devel')

        self.assertEqual(list(versions), [
            VersionInfo('post'),
            VersionInfo('devel'),
            VersionInfo('pre'),
            VersionInfo('beta'),
            VersionInfo('alpha'),
        ])

    def test_sort_versions_with_v_prefix(self):
        versions = Versions()
        versions.add('v0.2')
        versions.add('v0.10')
        versions.add('v1.0')
        versions.add('v2.0')
        versions.add('devel')

        self.assertEqual(list(versions), [
            VersionInfo('devel'),
            VersionInfo('v2.0'),
            VersionInfo('v1.0'),
            VersionInfo('v0.10'),
            VersionInfo('v0.2'),
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

    def test_add_alias_similar_to_version(self):
        versions = Versions()
        versions.add('1.0.0')
        v = versions.add('1.0.1', aliases=['1.0'])
        self.assertEqual(v, VersionInfo('1.0.1', aliases={'1.0'}))
        self.assertEqual(list(versions), [
            VersionInfo('1.0.1', aliases={'1.0'}),
            VersionInfo('1.0.0'),
        ])

    def test_add_circular_alias(self):
        versions = Versions()
        msg = '^duplicated version and alias$'
        with self.assertRaisesRegex(ValueError, msg):
            versions.add('1.0', aliases=['1.0'])

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

    def test_add_update_alias_similar_to_version(self):
        versions = Versions()
        versions.add('1.0.0', aliases=['1.0'])
        v = versions.add('1.0.1', aliases=['1.0'], update_aliases=True)
        self.assertEqual(v, VersionInfo('1.0.1', aliases={'1.0'}))
        self.assertEqual(list(versions), [
            VersionInfo('1.0.1', aliases={'1.0'}),
            VersionInfo('1.0.0'),
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

        msg = r"^alias 'latest' already exists for version '1\.0'$"
        with self.assertRaisesRegex(ValueError, msg):
            versions.update('2.0', aliases=['latest'])

    def test_update_circular_alias(self):
        versions = Versions()
        versions.add('1.0', aliases=['latest'])
        msg = '^duplicated version and alias$'
        with self.assertRaisesRegex(ValueError, msg):
            diff = versions.update('1.0', aliases=['1.0'])

        # This is ok, though it's a no-op, since the version is '1.0', and thus
        # there's no circularity.
        diff = versions.update('latest', aliases=['latest'])
        self.assertEqual(diff, set())
        self.assertEqual(list(versions), [
            VersionInfo('1.0', '1.0', ['latest']),
        ])

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

    def test_from_json(self):
        versions = Versions.from_json([
            {'version': '2.0', 'title': '2.0.2', 'aliases': ['latest']},
            {'version': '1.0', 'title': '1.0.1', 'aliases': ['stable']}
        ])
        self.assertEqual(list(versions), [
            VersionInfo('2.0', '2.0.2', aliases={'latest'}),
            VersionInfo('1.0', '1.0.1', aliases={'stable'}),
        ])

    def test_to_json(self):
        versions = Versions()
        versions.add('2.0', '2.0.2', ['latest'])
        versions.add('1.0', '1.0.1', ['stable'])
        self.assertEqual(versions.to_json(), [
            {'version': '2.0', 'title': '2.0.2', 'aliases': ['latest']},
            {'version': '1.0', 'title': '1.0.1', 'aliases': ['stable']}
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
