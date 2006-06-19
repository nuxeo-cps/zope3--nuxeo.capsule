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
"""Interfaces for Capsule

These interfaces represent the Capsule APIs.

Documents have properties holding data, and children. Documents are
typed. A type can be introspected to find its associated schema.

A schema is a Zope 3 interface with fields.
"""

from zope.interface import Interface
from zope.interface import Attribute

from zope.schema.interfaces import IMinMaxLen
from zope.schema.interfaces import IList
from zope.schema.interfaces import IObject

_MARKER = object()

##################################################
# Object: object having properties based on a schema

class IObjectBase(Interface):
    """An object with properties based on a schema.
    """

    def getSchema():
        """Get the schema on which this object is based.

        Returns a IInterface, whose fields describe the schema.

        The object also implements the interface in a standard manner
        for the component architecture.
        """

    def getTypeName():
        """Get the type of the object.

        Returns a unicode string.
        """

    def getProperties():
        """Get all the properties.

        Returns a mapping of name to a IProperty or a basic python type.
        """

    def getProperty(name, default=_MARKER):
        """Get a specific field.

        If the property doesn't exist, returns the default or raises
        KeyError if there is no default.

        Returns a IProperty or a basic python type.
        """

    def hasProperty(name):
        """Test if the document has a given property.

        Returns a boolean.
        """

    def setProperty(name, value):
        """Add a new property to the object or modify an existing one.

        If the value is None, the property is removed.
        """

##     def __getattr__(name):
##         """Get a specific field.
##
##         Returns a IProperty or a basic python type.
##         """


##################################################
# Properties

class IProperty(Interface):
    """Marker interface. A property stores actual data.

    In python, not all values are represented as properties, but the
    basic types (unicode, long, double, datetime, bool) are used
    directly.

    IProperty is used only for non-basic types, or for complex types.

    Properties are compared by object identity XXX or value?
    """

    def getName():
        """Get the name of the property.

        Returns a unicode string.
        """

    def setPythonValue(value):
        """Set the value of a property.

        `value` is a basic python datastructure.
        """

    def getPythonValue():
        """Get the value of a property.

        Returns a basic python datastructure.
        """


class IBinaryProperty(IProperty):
    """A binary object (blob).

    This is specified in a schema using a IBinaryField.
    """

    mime_type = Attribute("The MIME type for this binary")

    encoding = Attribute("The encoding type for this binary")

    def open():
        """Get a seekable file-like object for this binary.
        """

    def __len__():
        """Get the length of the binary.
        """

    def __str__():
        """Get a string containing the binary.
        """

class IListProperty(IProperty):
    """A complex type that is a list of values.

    Each value is a IObjectProperty.

    This is specified in a schema using a IListPropertyField.
    """

    def __getitem__(index):
        """Get the value at a given index.
        """

    def __len__():
        """Get the length of the list.
        """

    def __contains__(value):
        """Test containment.

        Compares by object identity.
        """

    def __iter__():
        """Get an iterator for the list.
        """

    def getValueSchema():
        """Get the schema for the values of this list.
        """

    def addValue():
        """Add a new empty value to the list.

        Returns an IProperty
        """

class IObjectProperty(IObjectBase, IProperty):
    """A complex type with fields based on a schema.

    This is specified in a schema using a IObjectPropertyField.
    """


class IReference(Interface):
    """A reference to another object by UUID.
    """
    def getTargetUUID():
        """Get the UUID to which this object refers.

        Returns a python string.
        """


##################################################
# Documents

class IDocument(IObjectBase):
    """Capsule document.
    """

    def getName():
        """Get the name.

        Returns a unicode string.
        """

    def getUUID():
        """Get the UUID for this document.

        Returns an ascii string.

        The UUID is unique to a document, and is kept during moves,
        checkins and checkouts.
        """

    def getParent():
        """Get the parent document.

        Returns a IDocument, or None for the root.
        """

    ##### Properties: see IObjectBase

    ##### Children

    def getChild(name, default=_MARKER):
        """Get a specific child.

        Returns a IDocument.

        If the child doesn't exist, returns the default or raises
        KeyError if there is no default.
        """

    def __getitem__(name):
        """Get a specific child.

        Returns a IDocument.

        Raises KeyError if the child doesn't exist.
        """

    def getChildren():
        """Get the children.

        Returns an iterable of children implementing IDocument.
        """

    def hasChild(name):
        """Test if the document has a given child.

        Returns a boolean.
        """

    def hasChildren():
        """Test if the document has any children.

        Returns a boolean.
        """

    def addChild(name, type_name):
        """Add a new empty child to the document.

        Returns the newly created IDocument.
        """

    def removeChild(name):
        """Remove a child from the document.
        """

    ##### Misc

    def isReadOnly():
        """Test if the document is read only.

        A document can be read only if it is checked in.
        """

    ##### Versioning

    def checkout():
        """Checkout
        """

    def checkin():
        """Checkin
        """

    def isCheckedOut():
        """Test if the document is checked out.
        """

    # def restore(version_or_label)

    # def getVersionHistory()

    # def getBaseVersion()


##################################################
# Children (internal implementation detail of the Document class)

class IChildren(Interface):
    """Holder of children nodes.

    Children all have distinct names, and can be ordered or not.
    """

    def getChild(name, default=_MARKER):
        """Get a specific child.

        Returns a IDocument.

        If the child doesn't exist, returns the default or raises
        KeyError if there is no default.
        """

    def __getitem__(name):
        """Get a specific child.

        Returns a IDocument.

        Raises KeyError if the child doesn't exist.
        """

    def getChildren():
        """Get the children.

        Returns an iterable of children implementing IDocument.
        """

    def __contains__(name):
        """Test containment by name.
        """

    def __len__():
        """Get the number of children.
        """

    def hasChildren():
        """Test if the document has any children.

        Returns a boolean.
        """

    def addChild(child):
        """Add a new child.

        Raises KeyError if a child with the same name already exists.
        """

    def removeChild(name):
        """Remove a child.

        Returns the child removed, or raises KeyError if it doesn't exist.
        """

##################################################
# Typing

class ISchemaManager(Interface):
    """A Schema Manager knows about registered schemas.

    It holds a schema and a class for each type name.
    """

    def getSchemas():
        """Get all the registered schemas.

        Returns a mapping of name to Interface.
        """

    def getSchema(name, default=_MARKER):
        """Get a schema corresponding to a schema name.

        Returns an Interface.
        """

    def getClass(name, default=_MARKER):
        """Get a class corresponding to a type name.

        Returns a class.
        """

    def addSchema(schema, klass=None):
        """Add a new schema.
        """

    def setClass(name, klass):
        """Set the class for an already defined schema.
        """

    def setDefaultClass(klass):
        """Set the default class.

        All schema currently using the default class will be fixed to
        any preexisting default.
        """

##################################################
# Schemas Fields

class ICapsuleField(Interface):
    """Marker interface for complex Capsule fields.
    """

class IBinaryField(IMinMaxLen, ICapsuleField):
    """Schema field containing a seekable file-like object.
    """

class IListPropertyField(IList, ICapsuleField):
    """Schema field containing a persistent list of objects.
    """

class IObjectPropertyField(IObject, ICapsuleField):
    """Schema field containing a schema-based object.
    """

class IReferenceField(Interface):
    """Schema field containing a capsule reference.
    """
