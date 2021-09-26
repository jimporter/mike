from unittest import TestCase

from mike import arguments


class TestParser(TestCase):
    def test_complete(self):
        p = arguments.ArgumentParser()
        arg = p.add_argument('--arg', complete='file')
        self.assertEqual(arg.complete, 'file')

    def test_complete_group(self):
        p = arguments.ArgumentParser()
        g = p.add_argument_group()
        arg = g.add_argument('--arg', complete='file')
        self.assertEqual(arg.complete, 'file')

    def test_complete_action(self):
        class MyAction(arguments.Action):
            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, values.upper())

        p = arguments.ArgumentParser()
        arg = p.add_argument('--arg', action=MyAction, complete='file')
        self.assertEqual(arg.complete, 'file')
        self.assertEqual(p.parse_args(['--arg=foo']),
                         arguments.Namespace(arg='FOO'))
