##############################################################################
#
# Copyright (c) 2006 Nuxeo and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
# Author: Florent Guillaume <fg@nuxeo.com>
# $Id$
"""Basic tests.
"""

import unittest
from zope.testing.doctest import DocTestSuite
from zope.interface.verify import verifyClass


class InterfaceTests(unittest.TestCase):

    def test_BinaryProperty(self):
        from nuxeo.capsule.interfaces import IBinaryProperty
        from nuxeo.capsule.base import BinaryProperty
        verifyClass(IBinaryProperty, BinaryProperty)

    def test_ListProperty(self):
        from nuxeo.capsule.interfaces import IListProperty
        from nuxeo.capsule.base import ListProperty
        verifyClass(IListProperty, ListProperty)

    def test_ObjectProperty(self):
        from nuxeo.capsule.interfaces import IObjectProperty
        from nuxeo.capsule.base import ObjectProperty
        verifyClass(IObjectProperty, ObjectProperty)

    def test_Document(self):
        from nuxeo.capsule.interfaces import IDocument
        from nuxeo.capsule.base import Document
        verifyClass(IDocument, Document)

    def test_Children(self):
        from nuxeo.capsule.interfaces import IChildren
        from nuxeo.capsule.base import Children
        verifyClass(IChildren, Children)

    def test_BinaryField(self):
        from nuxeo.capsule.interfaces import IBinaryField
        from nuxeo.capsule.field import BinaryField
        verifyClass(IBinaryField, BinaryField)

    def test_ListPropertyField(self):
        from nuxeo.capsule.interfaces import IListPropertyField
        from nuxeo.capsule.field import ListPropertyField
        verifyClass(IListPropertyField, ListPropertyField)

    def test_ObjectPropertyField(self):
        from nuxeo.capsule.interfaces import IObjectPropertyField
        from nuxeo.capsule.field import ObjectPropertyField
        verifyClass(IObjectPropertyField, ObjectPropertyField)

    def test_ReferenceField(self):
        from nuxeo.capsule.interfaces import IReferenceField
        from nuxeo.capsule.field import ReferenceField
        verifyClass(IReferenceField, ReferenceField)

    def test_SchemaManager(self):
        from nuxeo.capsule.interfaces import ISchemaManager
        from nuxeo.capsule.schema import SchemaManager
        verifyClass(ISchemaManager, SchemaManager)


    def test_Reference(self):
        from nuxeo.capsule.interfaces import IReference
        from nuxeo.capsule.base import Reference
        verifyClass(IReference, Reference)


def test_Reference():
    """
    >>> from nuxeo.capsule.base import Reference
    >>> r = Reference('abc-def')
    >>> r
    Reference('abc-def')
    >>> r.getTargetUUID()
    'abc-def'
    >>> cmp(r, None), cmp(None, r)
    (1, -1)
    >>> cmp(r, 123), cmp(123, r)
    (1, -1)
    >>> r1, r2 = Reference('abc'), Reference('abc')
    >>> r1 == r2, r1 is r2
    (True, False)

    """

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(InterfaceTests),
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
