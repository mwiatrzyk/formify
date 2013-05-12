import unittest

from formify.forms import xhtml


class TestMarkup(unittest.TestCase):

    def test_html(self):
        # When
        tag = xhtml.Markup('foo')
        # Then
        self.assertIs(tag, tag.__html__())

    def test_escape_safe(self):
        # Given
        value = xhtml.Markup('<safe>')
        # When
        escaped = xhtml.Markup.escape(value)
        # Then
        self.assertEqual(escaped, '<safe>')

    def test_escape_safe_with_html_method(self):
        # Given
        class Test(object):
            def __html__(self):
                return '<safe>'
        # When
        escaped = xhtml.Markup.escape(Test())
        # Then
        self.assertEqual(escaped, '<safe>')

    def test_escape_unsafe(self):
        # When
        escaped = xhtml.Markup.escape('<>')
        # Then
        self.assertEqual(escaped, '&lt;&gt;')


class TestTag(unittest.TestCase):

    def test_constructor(self):
        # When
        tag = xhtml.Tag('test', 'data', 'cdata', {'foo': 'bar'})
        # Then
        self.assertEqual(tag.name, 'test')
        self.assertEqual(tag.data, 'data')
        self.assertEqual(tag.cdata, 'cdata')
        self.assertEqual(tag.attr, {'foo': 'bar'})

    def test_repr(self):
        # When
        tag = xhtml.Tag('br')
        # Then
        self.assertEqual(repr(tag), "u'<br/>'")

    def test_str(self):
        # When
        tag = xhtml.Tag('br')
        # Then
        self.assertEqual(repr(str(tag)), "'<br/>'")

    def test_unicode(self):
        # When
        tag = xhtml.Tag('br')
        # Then
        self.assertEqual(repr(unicode(tag)), "u'<br/>'")

    def test_attr(self):
        # When
        tag = xhtml.Tag('a', attr={'href': '/foo/bar/baz?a=1&b=2'})
        # Then
        self.assertEqual(unicode(tag), '<a href="/foo/bar/baz?a=1&amp;b=2"/>')

    def test_data_iterable(self):
        # When
        tag = xhtml.Tag('a', ['test', 'iterable', '<>&"'])
        # Then
        self.assertEqual(unicode(tag), '<a>testiterable&lt;&gt;&amp;&quot;</a>')

    def test_data_iterable_nested_tag(self):
        # Given
        nested = xhtml.Tag('br')
        # When
        tag = xhtml.Tag('a', ['before', nested, 'after'])
        # Then
        self.assertEqual(unicode(tag), '<a>before<br/>after</a>')

    def test_data_noniterable(self):
        # When
        tag = xhtml.Tag('a', '')
        # Then
        self.assertEqual(unicode(tag), '<a></a>')

    def test_cdata_iterable(self):
        # When
        tag = xhtml.Tag('a', cdata=['test', 'iterable', '<>&"'])
        # Then
        self.assertEqual(unicode(tag), '<a><![CDATA[testiterable<>&"]]></a>')

    def test_cdata_iterable_nested_tag(self):
        # Given
        nested = xhtml.Tag('br')
        # When
        tag = xhtml.Tag('a', cdata=['before', nested, 'after'])
        # Then
        self.assertEqual(unicode(tag), '<a><![CDATA[before<br/>after]]></a>')

    def test_cdata_noniterable(self):
        # When
        tag = xhtml.Tag('a', cdata='foo')
        # Then
        self.assertEqual(unicode(tag), '<a><![CDATA[foo]]></a>')
