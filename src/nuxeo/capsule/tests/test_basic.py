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
from zope.interface.verify import verifyClass


class InterfaceTests(unittest.TestCase):

    def test_BinaryProperty(self):
        from nuxeo.capsule.interfaces import IBinaryProperty
        from nuxeo.capsule import BinaryProperty
        verifyClass(IBinaryProperty, BinaryProperty)

    def test_ListProperty(self):
        from nuxeo.capsule.interfaces import IListProperty
        from nuxeo.capsule import ListProperty
        verifyClass(IListProperty, ListProperty)

    def test_ObjectProperty(self):
        from nuxeo.capsule.interfaces import IObjectProperty
        from nuxeo.capsule import ObjectProperty
        verifyClass(IObjectProperty, ObjectProperty)

    def test_Document(self):
        from nuxeo.capsule.interfaces import IDocument
        from nuxeo.capsule import Document
        verifyClass(IDocument, Document)

    def test_BinaryField(self):
        from nuxeo.capsule.interfaces import IBinaryField
        from nuxeo.capsule.field import BinaryField
        verifyClass(IBinaryField, BinaryField)

    def test_ListPropertyField(self):
        from nuxeo.capsule.interfaces import IListPropertyField
        from nuxeo.capsule.field import ListPropertyField
        verifyClass(IListPropertyField, ListPropertyField)

    def test_Type(self):
        from nuxeo.capsule.interfaces import IType
        from nuxeo.capsule.type import Type
        verifyClass(IType, Type)

    def test_TypeManager(self):
        from nuxeo.capsule.interfaces import ITypeManager
        from nuxeo.capsule.type import TypeManager
        verifyClass(ITypeManager, TypeManager)

    def test_SchemaManager(self):
        from nuxeo.capsule.interfaces import ISchemaManager
        from nuxeo.capsule.schema import SchemaManager
        verifyClass(ISchemaManager, SchemaManager)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(InterfaceTests),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
