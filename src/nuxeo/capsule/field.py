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
from zope.schema import MinMaxLen
from zope.schema import List
from zope.schema import Object

from nuxeo.capsule.interfaces import IBinaryField
from nuxeo.capsule.interfaces import IListPropertyField
from nuxeo.capsule.interfaces import IObjectPropertyField

from nuxeo.capsule import BinaryProperty
from nuxeo.capsule import ListProperty
from nuxeo.capsule import ObjectProperty


class BinaryField(MinMaxLen, Field):
    """A field containing a python file-like seekable object.
    """
    zope.interface.implements(IBinaryField)
    _type = BinaryProperty


class ListPropertyField(List):
    """A field representing a persistent List of properties.
    """
    zope.interface.implements(IListPropertyField)
    _type = ListProperty

class ObjectPropertyField(Object):
    """A field representing a persistent object.
    """
    zope.interface.implements(IObjectPropertyField)
    _type = ObjectProperty
