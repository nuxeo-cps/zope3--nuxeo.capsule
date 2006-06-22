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
"""Capsule Schemas.
"""

import zope.interface
from zope.interface.interfaces import IInterface
from nuxeo.capsule.interfaces import ISchemaManager

_MARKER = object()

class SchemaManager(object):
    """A Schema Manager knows about registered schemas.

    Each schema may be tied to a class too.
    """
    zope.interface.implements(ISchemaManager)

    def __init__(self):
        self._clear()

    def _clear(self):
        self._schemas = {} # all schemas including aliases
        self._schemas_unaliased = set() # no aliases here
        self._classes = {}
        self._default_class = None

    def getSchemas(self):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        return dict((name, self._schemas[name])
                    for name in self._schemas_unaliased)

    def getSchema(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        try:
            return self._schemas[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    def getClass(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        try:
            klass = self._classes[name]
            if klass is None:
                klass = self._default_class
                if klass is None:
                    raise KeyError(name)
        except KeyError:
            if default is not _MARKER:
                return default
            raise
        return klass

    # Management

    def _addSchema(self, name, schema):
        if name in self._schemas:
            raise ValueError("Schema %r already registered" % name)
        if not IInterface.providedBy(schema):
            raise ValueError("Schema %r is not an Interface" % name)
        self._schemas[name] = schema
        if name not in self._classes:
            self._classes[name] = None

    def addSchema(self, name, schema):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        self._addSchema(name, schema)
        self._schemas_unaliased.add(name)
        if name != schema.getName():
            self._addSchema(schema.getName(), schema)

    def setClass(self, name, klass):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        if self._classes.get(name) is not None:
            raise ValueError("Class %r already registered" % name)
        self._classes[name] = klass

    def setDefaultClass(self, klass):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        if self._default_class is not None:
            for name, k in self._classes.iteritems():
                if k is None:
                    self._classes[name] = self._default_class
        self._default_class = klass
