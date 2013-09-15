import unittest

from formify.schema import Schema
from formify.validators import String, Integer
from formify.validators.grouping import Group


class TestGroup(unittest.TestCase):

    def setUp(self):

        class GroupedSchema(Schema):
            foo = String()
            bar = Integer()

        self.GroupedSchema = GroupedSchema

    def create_group_from_schema(self):
        return Group(self.GroupedSchema)

    def create_schema(self):
        class WrappingSchema(Schema):
            baz = Group(self.GroupedSchema)
        return WrappingSchema()

    def test_ok(self):
        # Given
        group = self.create_schema()
        group.baz.bar = '123'
        group.baz.foo = 'ala ma kota'
        print repr(group.baz.foo)
        print repr(group['baz']['foo'].value)
        self.assertFalse(True)
