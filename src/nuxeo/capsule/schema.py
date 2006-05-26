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
    """
    zope.interface.implements(ISchemaManager)

    def __init__(self):
        self._schemas = {}

    def getSchemas(self):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        return self._schemas.copy()

    def getSchema(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.ISchemaManager`
        """
        try:
            return self._schemas[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    # Management

    def addSchema(self, name, schema):
        if name in self._schemas:
            raise ValueError("Schema %r already registered" % name)
        if not IInterface.providedBy(schema):
            raise ValueError("Schema %r is not an Interface" % name)
        self._schemas[name] = schema
