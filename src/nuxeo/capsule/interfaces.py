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

import zope.app.container.constraints
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

class IContainerBase(Interface):
    """An object containing children.
    """

    def getChild(name, default=_MARKER):
        """Get a specific child.

        Returns a IObjectBase.

        If the child doesn't exist, returns the default or raises
        KeyError if there is no default.
        """

    def __getitem__(name):
        """Get a specific child.

        Returns a IObjectBase.

        Raises KeyError if the child doesn't exist.
        """

    def getChildren():
        """Get the children.

        Returns an iterable of children implementing IObjectBase.
        """

    def keys():
        """Get the list of children names.
        """

    def __iter__():
        """Get an iterable of children.
        """

    def hasChild(name):
        """Test if the document has a given child.

        Returns a boolean.
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

    def addChild(name, type_name):
        """Add a new empty child to the document.

        `type_name` may be a schema itself instead of a string.

        Returns the newly created IObjectBase.

        Raises KeyError if a child with the same name already exists.
        """

    def removeChild(name):
        """Remove a child.
        """

    def __delitem__(name):
        """Remove a child.
        """

    def clear():
        """Remove all children.
        """

    def reorder(names):
        """Reorder the children.

        `names` must be a permutation of the current names.
        """


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

    def setDTO(value):
        """Set a property from a DTO.

        `value` is a Data Transfer Object, usually a basic python
        datastructure.
        """

    def getDTO():
        """Get a DTO from a property.

        Returns a Data Transfer Object, usually a basic python datastructure.
        """


class IObjectProperty(IObjectBase, IProperty):
    """A complex type with fields based on a schema.
    """


class IContainerProperty(IObjectProperty, IContainerBase):
    """A complex type holding subobjects.
    """


class IListProperty(IContainerProperty):
    """A complex type that is a list of values.

    The schema of the values is constrained.
    """

    def __getitem__(index):
        """Get the value at a given index.
        """

    def __delitem__(index):
        """Remove the value at a given index.
        """

    def __len__():
        """Get the length of the list.
        """

    def __contains__(value):
        """Test containment.

        Compares by object identity.
        """

    def getValueSchema():
        """Get the schema for the values of this list.
        """

    def addValue():
        """Add a new empty value to the list.

        Returns an IProperty
        """

class IResourceProperty(IObjectProperty):
    """A resource property.

    Designed to hold a JCR nt:resource.
    """

    #Injected later: from field.py
    # jcr:data (Binary)
    # jcr:mimeType (String)
    # jcr:encoding (String)
    # jcr:lastModified (Date)

class IResource(Interface):
    """A binary object.

    This is the DTO of a IResourceProperty.
    """

    mime_type = Attribute("The MIME type for this resource")

    encoding = Attribute("The encoding type for this resource")

    def __len__():
        """Get the length of the resource.
        """

    def __str__():
        """Get a string containing the resource.
        """

    def open():
        """Get a seekable file-like object for this resource.
        """

    def getFileUpload():
        """Get a (fake) file upload for this resource.
        """


class IBlob(Interface):
    """A blob.

    This is the DTO of a JCR Binary property.
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

class IDocument(IObjectBase, IContainerBase):
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

        XXX semantics for children of ListProperty?
        """

    ##### Properties: see IObjectBase

    ##### Children: see IContainerBase

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

    ##### Search

    def locateUUID(uuid):
        """Get the path of a doc with a given UUID.

        Return None if the UUID does not exist.

        The path is relative to the JCR workspace root.
        """

    def searchProperty(prop_name, value):
        """Search the JCR for nodes where prop_name == 'value'.

        Returns a sequence of (uuid, path).

        The paths are relative to the JCR workspace root.
        """

    # def restore(version_or_label)

    # def getVersionHistory()

    # def getBaseVersion()


class IVersionHistory(IDocument):
    """Capsule version history.
    """

class IVersion(IDocument):
    """Capsule version.
    """

class IFrozenNode(IDocument):
    """Capsule frozen node.
    """

class IProxy(IDocument):
    """Capsule proxy.
    """

class IWorkspace(IDocument):
    """Capsule workspace, root of a tree of documents.
    """


##################################################
# Children (internal implementation detail of the Document class)

class IChildren(IContainerBase):
    """Holder of children nodes.

    Children all have distinct names, and can be ordered or not.
    """

    zope.app.container.constraints.contains(IDocument)

    def getTypeName():
        """Get the type of this intermediate object.
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

        The class returned will be the class set by `setClass` for the
        most specific base schema for that name.

        Returns a class.
        """

    def addSchema(name, schema):
        """Add a new schema.
        """

    def setClass(name, klass):
        """Set the class for a schema and its derived ones.
        """


##################################################
# Schemas Fields

class ICapsuleField(Interface):
    """Marker interface for complex Capsule fields.
    """


class IObjectPropertyField(IObject, ICapsuleField):
    """Schema field for a capsule object.
    """

class IContainerPropertyField(IObjectPropertyField):
    """Schema field for a capsule container.
    """

class IListPropertyField(IContainerPropertyField, IList):
    """Schema field for a persistent list of objects.
    """


class IBlobField(Interface):
    """Schema field containing a blob.
    """

class IReferenceField(Interface):
    """Schema field containing a capsule reference.
    """
