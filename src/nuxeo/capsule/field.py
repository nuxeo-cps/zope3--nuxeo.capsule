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
"""Specific fields.
"""

import zope.interface
from zope.schema import Field
from zope.schema import Text
from zope.schema import Datetime
from zope.schema import MinMaxLen
from zope.schema import List
from zope.schema import Object

from nuxeo.capsule.interfaces import IObjectPropertyField
from nuxeo.capsule.interfaces import IContainerPropertyField
from nuxeo.capsule.interfaces import IListPropertyField
from nuxeo.capsule.interfaces import IBlobField
from nuxeo.capsule.interfaces import IReferenceField

from nuxeo.capsule.base import ObjectProperty
from nuxeo.capsule.base import ContainerProperty
from nuxeo.capsule.base import ListProperty
from nuxeo.capsule.base import ResourceProperty
from nuxeo.capsule.base import Blob
from nuxeo.capsule.base import Reference


class ObjectPropertyField(Object):
    """A field representing a capsule object.

    A capsule object has a schema and can hold properties.
    This field holds a `schema` attribute.
    """
    zope.interface.implements(IObjectPropertyField)
    _type = ObjectProperty


class ContainerPropertyField(ObjectPropertyField, List):
    """A field representing a container.

    This field holds a `schema` attribute.
    """
    zope.interface.implements(IContainerPropertyField)
    _type = ContainerProperty


class ListPropertyField(ContainerPropertyField):
    """A field representing a persistent List of properties.

    This field holds a `schema` attribute and a `value_type` attribute.
    """
    zope.interface.implements(IListPropertyField)
    _type = ListProperty
    def __init__(self, schema, **kw):
        ContainerPropertyField.__init__(self, schema, **kw)
        types = schema['__setitem__'].getTaggedValue('precondition').types
        assert len(types) == 1, types
        value_schema = types[0]
        subfield = ObjectPropertyField(value_schema, __name__='')
        List.__init__(self, value_type=subfield, **kw)


class BlobField(MinMaxLen, Field):
    """A field containing a python file-like seekable object.
    """
    zope.interface.implements(IBlobField)
    _type = Blob


class ReferenceField(Field):
    """A field containing a capsule reference.
    """
    zope.interface.implements(IReferenceField)
    _type = Reference


# Inject fields into IResourceProperty
from nuxeo.capsule.interfaces import IResourceProperty
attrs = IResourceProperty._InterfaceClass__attrs
for name, klass in (
    ('jcr:data', BlobField),
    ('jcr:mimeType', Text),
    ('jcr:encoding', Text),
    ('jcr:lastModified', Datetime),
    ):
    field = klass(__name__=name)
    field.interface = IResourceProperty
    attrs[name] = field
del field, attrs, name, klass
