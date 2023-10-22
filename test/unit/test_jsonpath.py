import unittest
from copy import deepcopy

from mike import jsonpath


class TestParse(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(jsonpath.parse(''), [])

    def test_field(self):
        self.assertEqual(jsonpath.parse('field'), ['field'])
        self.assertEqual(jsonpath.parse('"field"'), ['field'])
        self.assertEqual(jsonpath.parse("'field'"), ['field'])
        self.assertEqual(jsonpath.parse('"my.field"'), ['my.field'])
        self.assertEqual(jsonpath.parse("'my.field'"), ['my.field'])
        self.assertEqual(jsonpath.parse('"0"'), ['0'])
        self.assertEqual(jsonpath.parse("'0'"), ['0'])

    def test_index(self):
        self.assertEqual(jsonpath.parse('[0]'), [0])
        self.assertEqual(jsonpath.parse('[-1]'), [-1])
        self.assertEqual(jsonpath.parse('[head]'), [jsonpath.head])
        self.assertEqual(jsonpath.parse('[tail]'), [jsonpath.tail])

    def test_field_index(self):
        self.assertEqual(jsonpath.parse('["field"]'), ['field'])
        self.assertEqual(jsonpath.parse("['field']"), ['field'])
        self.assertEqual(jsonpath.parse('["my.field"]'), ['my.field'])
        self.assertEqual(jsonpath.parse("['my.field']"), ['my.field'])
        self.assertEqual(jsonpath.parse('["0"]'), ['0'])
        self.assertEqual(jsonpath.parse("['0']"), ['0'])

    def test_steps(self):
        self.assertEqual(jsonpath.parse('foo.bar'), ['foo', 'bar'])
        self.assertEqual(jsonpath.parse('foo[1].bar'), ['foo', 1, 'bar'])
        self.assertEqual(jsonpath.parse('"foo.bar".baz'), ['foo.bar', 'baz'])

    def test_whitespace(self):
        self.assertEqual(jsonpath.parse(' '), [])
        self.assertEqual(jsonpath.parse(' foo [ 1 ] . bar '),
                         ['foo', 1, 'bar'])


class TestParseSet(unittest.TestCase):
    def test_empty_path(self):
        self.assertEqual(jsonpath.parse_set('='), ([], ''))
        self.assertEqual(jsonpath.parse_set('=val'), ([], 'val'))

    def test_field(self):
        self.assertEqual(jsonpath.parse_set('field=val'), (['field'], 'val'))
        self.assertEqual(jsonpath.parse_set('"fi=ld"=val'), (['fi=ld'], 'val'))
        self.assertEqual(jsonpath.parse_set("'fi=ld'=val"), (['fi=ld'], 'val'))

    def test_index(self):
        self.assertEqual(jsonpath.parse_set('[0]=val'), ([0], 'val'))
        self.assertEqual(jsonpath.parse_set('[-1]=val'), ([-1], 'val'))
        self.assertEqual(jsonpath.parse_set('[head]=val'),
                         ([jsonpath.head], 'val'))
        self.assertEqual(jsonpath.parse_set('[tail]=val'),
                         ([jsonpath.tail], 'val'))

    def test_field_index(self):
        self.assertEqual(jsonpath.parse_set('["fi=ld"]=val'),
                         (['fi=ld'], 'val'))
        self.assertEqual(jsonpath.parse_set("['fi=ld']=val"),
                         (['fi=ld'], 'val'))

    def test_steps(self):
        self.assertEqual(jsonpath.parse_set('foo.bar=val'),
                         (['foo', 'bar'], 'val'))
        self.assertEqual(jsonpath.parse_set('foo[1].bar=val'),
                         (['foo', 1, 'bar'], 'val'))
        self.assertEqual(jsonpath.parse_set('"foo.bar".baz=val'),
                         (['foo.bar', 'baz'], 'val'))

    def test_whitespace(self):
        self.assertEqual(jsonpath.parse_set(' foo [ 1 ] . bar = val '),
                         (['foo', 1, 'bar'], 'val '))


class TestGetValue(unittest.TestCase):
    def test_scalar(self):
        self.assertEqual(jsonpath.get_value(42, ''), 42)

    def test_list(self):
        self.assertEqual(jsonpath.get_value(['a', 'b', 'c'], '[1]'), 'b')
        self.assertEqual(jsonpath.get_value(['a', 'b', 'c'], '[-1]'), 'c')

    def test_dict(self):
        self.assertEqual(jsonpath.get_value({'a': 2, 'b': 4, 'c': 6}, 'b'), 4)

    def test_missing(self):
        self.assertEqual(jsonpath.get_value(['a', 'b', 'c'], '[3]'), None)
        self.assertEqual(jsonpath.get_value({'a': 2, 'b': 4, 'c': 6}, 'd'),
                         None)

    def test_missing_strict(self):
        with self.assertRaises(IndexError):
            jsonpath.get_value(['a', 'b', 'c'], '[3]', strict=True)
        with self.assertRaises(KeyError):
            jsonpath.get_value({'a': 2, 'b': 4, 'c': 6}, 'd', strict=True)

    def test_nested(self):
        data = {'zoo': {'goat': ['billy'], 'redpanda': ['adira', 'pavitra']}}
        self.assertEqual(jsonpath.get_value(data, 'zoo.redpanda[1]'),
                         'pavitra')
        expr = jsonpath.parse('zoo.goat[0]')
        self.assertEqual(jsonpath.get_value(data, expr), 'billy')

    def test_incompatible(self):
        with self.assertRaises(TypeError):
            jsonpath.get_value(42, 'field')
        with self.assertRaises(TypeError):
            jsonpath.get_value([0, 1, 2], 'field')
        with self.assertRaises(TypeError):
            jsonpath.get_value({'a': 2}, '[0]')

    def test_head_tail(self):
        with self.assertRaises(TypeError):
            jsonpath.get_value([], '[head]')
        with self.assertRaises(TypeError):
            jsonpath.get_value([], '[tail]')


class TestSetValue(unittest.TestCase):
    def test_scalar(self):
        self.assertEqual(jsonpath.set_value(True, '', 42), 42)

    def test_list(self):
        self.assertEqual(jsonpath.set_value(['a', 'b', 'c'], '[1]', 'd'),
                         ['a', 'd', 'c'])
        self.assertEqual(jsonpath.set_value(['a', 'b', 'c'], '[-1]', 'd'),
                         ['a', 'b', 'd'])
        self.assertEqual(jsonpath.set_value(['a', 'b', 'c'], '[head]', 'z'),
                         ['z', 'a', 'b', 'c'])
        self.assertEqual(jsonpath.set_value(['a', 'b', 'c'], '[tail]', 'd'),
                         ['a', 'b', 'c', 'd'])

    def test_dict(self):
        self.assertEqual(jsonpath.set_value({'a': 2, 'b': 4, 'c': 6}, 'b', 40),
                         {'a': 2, 'b': 40, 'c': 6})
        self.assertEqual(jsonpath.set_value({'a': 2, 'b': 4, 'c': 6}, 'd', 8),
                         {'a': 2, 'b': 4, 'c': 6, 'd': 8})

    def test_collapse(self):
        self.assertEqual(jsonpath.set_value(['a', 'b', 'c'], '', 42), 42)

    def test_none(self):
        self.assertEqual(jsonpath.set_value(None, 'foo.bar[0][1].baz', 42),
                         {'foo': {'bar': [[None, {'baz': 42}]]}})

    def test_incompatible(self):
        with self.assertRaises(TypeError):
            jsonpath.set_value(42, 'field', 'value')
        with self.assertRaises(TypeError):
            jsonpath.set_value([0, 1, 2], 'field', 'value')
        with self.assertRaises(TypeError):
            jsonpath.set_value({'a': 2}, '[0]', 'value')

    def test_nonlast_head_tail(self):
        with self.assertRaises(TypeError):
            jsonpath.set_value([], '[head].foo', 'value')
        with self.assertRaises(TypeError):
            jsonpath.set_value([], '[tail].foo', 'value')


class TestDeleteValue(unittest.TestCase):
    @staticmethod
    def call(data, path, **kwargs):
        return jsonpath.delete_value(data, path, **kwargs)

    def test_scalar(self):
        self.assertEqual(self.call(True, ''), None)

    def test_list(self):
        self.assertEqual(self.call(['a', 'b', 'c'], '[1]'), ['a', 'c'])
        self.assertEqual(self.call(['a', 'b', 'c'], '[-1]'), ['a', 'b'])

    def test_dict(self):
        self.assertEqual(self.call({'a': 2, 'b': 4, 'c': 6}, 'b'),
                         {'a': 2, 'c': 6})

    def test_nested(self):
        data = {'zoo': {'goat': ['billy'], 'redpanda': ['adira', 'pavitra']}}
        self.assertEqual(
            self.call(deepcopy(data), 'zoo.redpanda[1]'),
            {'zoo': {'goat': ['billy'], 'redpanda': ['adira']}}
        )
        self.assertEqual(
            self.call(deepcopy(data), 'zoo.goat'),
            {'zoo': {'redpanda': ['adira', 'pavitra']}}
        )
        self.assertEqual(self.call(deepcopy(data), 'zoo'), {})
        self.assertEqual(self.call(deepcopy(data), ''), None)

        expr = jsonpath.parse('zoo.goat[0]')
        self.assertEqual(
            self.call(deepcopy(data), expr),
            {'zoo': {'goat': [], 'redpanda': ['adira', 'pavitra']}}
        )

    def test_missing(self):
        self.assertEqual(self.call(['a', 'b', 'c'], '[3]'),
                         ['a', 'b', 'c'])
        self.assertEqual(self.call({'a': 2, 'b': 4, 'c': 6}, 'd'),
                         {'a': 2, 'b': 4, 'c': 6})
        self.assertEqual(self.call(['a', 'b', 'c'], '[3].foo'),
                         ['a', 'b', 'c'])

    def test_missing_strict(self):
        with self.assertRaises(IndexError):
            self.call(['a', 'b', 'c'], '[3]', strict=True)
        with self.assertRaises(KeyError):
            self.call({'a': 2, 'b': 4, 'c': 6}, 'd', strict=True)
        with self.assertRaises(IndexError):
            self.call(['a', 'b', 'c'], '[3].foo', strict=True)

    def test_head_tail(self):
        with self.assertRaises(TypeError):
            self.call([], '[head]')
        with self.assertRaises(TypeError):
            self.call([], '[tail]')


class TestDeleteValueUsingSet(TestDeleteValue):
    @staticmethod
    def call(data, path, **kwargs):
        return jsonpath.set_value(data, path, jsonpath.Deleted, **kwargs)
