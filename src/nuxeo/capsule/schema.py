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
        self._classes_spec = {} # spec of name -> class
        self._classes = {} # resolved name -> class, None means KeyError

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

        Finds the most specific registered schema extending the
        one passed, and returns the corresponding class.
        """
        try:
            if name in self._classes:
                klass = self._classes[name]
            else:
                # Find most specific schema extending the one passed
                if name not in self._schemas:
                    print 'XXX %s not in schemas!' % name
                schema = self._schemas[name]
                klass = None
                for n, k in self._classes_spec.iteritems():
                    if n not in self._schemas:
                        #print 'XXX %s in classes but not schemas!' % n
                        continue
                    s = self._schemas[n]
                    if schema.isOrExtends(s):
                        if klass is None or s.extends(best):
                            klass = k
                            best = s
                self._classes[name] = klass
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
            if self._schemas[name] == schema:
                return
            raise ValueError("Schema %r already registered for %r" %
                             (name, self._schemas[name]))
        if not IInterface.providedBy(schema):
            raise ValueError("Schema %r is not an Interface" % name)
        self._schemas[name] = schema

    def addSchema(self, name, schema):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        self._addSchema(name, schema)
        self._schemas_unaliased.add(name)
        if name != schema.getName():
            self._addSchema(schema.getName(), schema)
        self._classes = {}

    def setClass(self, name, klass):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        if name in self._classes_spec:
            prev = self._classes_spec[name]
            if issubclass(prev, klass):
                # Previous definition is already a subclass, keep it
                return
            if not issubclass(klass, prev):
                raise ValueError("Redefinition of type %r from %r to %r" %
                                 (name, prev, klass))
            # New definition can override the old one
        self._classes_spec[name] = klass
        self._classes = {}
