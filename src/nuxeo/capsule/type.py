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
"""Capsule Types.
"""

import zope.interface
from nuxeo.capsule.interfaces import IType
from nuxeo.capsule.interfaces import ITypeManager


class TypeManager(object):
    """A Type Manager knows about registered document types.
    """
    zope.interface.implements(ITypeManager)

    def __init__(self):
        self._types = {}

    def getTypes(self):
        """See `nuxeo.capsule.interfaces.ITypeManager`
        """
        return self._types.copy()

    def getType(self, name):
        """See `nuxeo.capsule.interfaces.ITypeManager`
        """
        return self._types[name]

    # Management

    def addType(self, type):
        name = type.getName()
        if name in self._types:
            raise ValueError("Type %r already registered" % name)
        if not IType.providedBy(type):
            raise ValueError("Provided type for %r is not a IType" % name)
        self._types[name] = type


class Type(object):
    """Capsule type.
    """
    zope.interface.implements(IType)

    def __init__(self, name, schema, container=False, ordered=False):
        self._name = name
        self._schema = schema
        self._is_container = container
        self._is_ordered = ordered

    def getName(self):
        """See `nuxeo.capsule.interfaces.IType`
        """
        return self._name

    def getSchema(self):
        """See `nuxeo.capsule.interfaces.IType`
        """
        return self._schema

    def isContainer(self):
        """See `nuxeo.capsule.interfaces.IType`
        """
        return self._is_container

    def isOrderedContainer(self):
        """See `nuxeo.capsule.interfaces.IType`
        """
        return self._is_ordered
