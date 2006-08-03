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
"""Capsule basic implementation.
"""

import re
import logging
import time
from datetime import datetime
from cStringIO import StringIO

import Acquisition
from Acquisition import aq_base
from persistent import Persistent

import zope.interface
from nuxeo.capsule.interfaces import IObjectBase
from nuxeo.capsule.interfaces import IContainerBase
from nuxeo.capsule.interfaces import IDocument
from nuxeo.capsule.interfaces import IWorkspace
from nuxeo.capsule.interfaces import IChildren

from nuxeo.capsule.interfaces import IProperty
from nuxeo.capsule.interfaces import IObjectProperty
from nuxeo.capsule.interfaces import IContainerProperty
from nuxeo.capsule.interfaces import IListProperty
from nuxeo.capsule.interfaces import IResourceProperty

from nuxeo.capsule.interfaces import IResource
from nuxeo.capsule.interfaces import IBlob
from nuxeo.capsule.interfaces import IReference

# Zope 2
View = 'View'
ModifyPortalContent = 'Modify portal content'
try:
    from Globals import InitializeClass
    from AccessControl import ClassSecurityInfo
except ImportError:
    class ClassSecurityInfo(object):
        def declarePrivate(self, arg): pass
        def declarePublic(self, arg): pass
        def declareProtected(self, *args): pass
        def declareObjectPublic(self): pass
        def setDefaultAccess(self, arg): pass
    def InitializeClass(klass):
        del klass.security


_MARKER = object()

logger = logging.getLogger('nuxeo.capsule.base')


class ObjectBase(Persistent):
    """A complex object with properties based on a schema.

    Properties are stored in the _props dict. Their value is either a
    python simple type, or an IProperty.
    """
    zope.interface.implements(IObjectBase)
    security = ClassSecurityInfo()

    __parent__ = None

    def __init__(self, name, schema):
        self.__name__ = name
        self._setSchema(schema)
        self._props = {}

    def _setSchema(self, schema):
        self._schema = schema

    security.declarePrivate('getSchema')
    def getSchema(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self._schema

    security.declareProtected(View, 'getTypeName')
    def getTypeName(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self.getSchema().getName()

    security.declareProtected(View, 'getProperties')
    def getProperties(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self._props.copy()

    security.declareProtected(View, 'getProperty')
    def getProperty(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        try:
            return self._props[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    security.declareProtected(View, 'hasProperty')
    def hasProperty(self, name):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return name in self._props

    security.declareProtected(ModifyPortalContent, 'setProperty')
    def setProperty(self, name, value):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        if value is None:
            if name in self._props:
                self._p_changed = True
                del self._props[name]
        else:
            self._p_changed = True
            self._props[name] = value

InitializeClass(ObjectBase)


class ContainerBase(Persistent):
    """A holder of children nodes.

    Children all have distinct names, and can be ordered or not.

    Children are stored inside the _children attribute, which maps a
    unicode name to a IObjectBase.

    For ordered containers, the _order list contains the ordered list of
    keys. For unordered containers, _order is None.

    For unordered containers, the children may be loaded lazily from the
    storage (because these containers can be big). In this case:

    - _lazy is a set storing the names of already loaded children,

    - _missing is a set storing the names of nonexistent children.

    If child loading is not lazy, _lazy and _missing are None.
    """
    zope.interface.implements(IContainerBase)
    security = ClassSecurityInfo()

    __parent__ = None
    _lazy = None
    _missing = None

    def __init__(self, name):
        self.__name__ = name
        self._children = {}
        self._order = [] # ordered XXX

    def _getPath(self, first=False):
        if self.__parent__ is None:
            return (self.__name__,)
        else:
            return self.__parent__._getPath() + (self.__name__,)

    def __repr__(self):
        path = '/'.join(self._getPath(True))
        return '<%s at %s>' % (self.__class__.__name__, path)

    security.declarePrivate('getChild')
    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        try:
            return self._children[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    def __setitem__(self, name, value):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        raise NotImplementedError("Not expected to be implemented")

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children[name]

    security.declarePrivate('getChildren')
    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return iter(self)

    security.declareProtected(View, 'keys')
    def keys(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if self._order is None:
            return self._children.keys()
        else:
            return list(self._order)

    def __iter__(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if self._order is None:
            return self._children.itervalues()
        else:
            return (self._children[k] for k in self._order)

    security.declareProtected(View, 'hasChild')
    def hasChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return name in self._children

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    security.declareProtected(View, 'hasChildren')
    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return bool(self._children)

    security.declarePrivate('addChild')
    def addChild(self, name, type_name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        raise NotImplementedError("Must be subclassed")

    security.declareProtected(ModifyPortalContent, 'removeChild')
    def removeChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        child = self._children[name]
        del self._children[name]
        if self._order is not None:
            self._order.remove(name)
        return child

    def __delitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self.removeChild(name)

    security.declareProtected(ModifyPortalContent, 'clear')
    def clear(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children = {}
        if self._order is not None:
            self._order = []

    security.declareProtected(ModifyPortalContent, 'reorder')
    def reorder(self, names):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if self._order is None:
            raise TypeError("Unordered container")
        if set(names) != set(self._order):
            raise ValueError("Names mismatch (%s to %s)" %
                             (self._order, names))
        self._order = list(names)

InitializeClass(ContainerBase)


class Children(ContainerBase):
    """Holder of children nodes.
    """
    zope.interface.implements(IChildren)
    security = ClassSecurityInfo()

    def __init__(self, name, schema=None):
        assert name == 'ecm:children', name
        ContainerBase.__init__(self, 'ecm:children')

    security.declareProtected(View, 'getName')
    def getName(self):
        return self.__name__

    security.declareProtected(View, 'getTypeName')
    def getTypeName(self):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        raise NotImplementedError

    def _getPath(self, first=False):
        if self.__parent__ is None:
            return (self.__name__,)
        ppath = self.__parent__._getPath()
        if first:
            return ppath + (self.__name__,)
        else:
            return ppath

InitializeClass(Children)


class Document(ObjectBase, Acquisition.Implicit):
    """Capsule Document.

    Properties
    ----------

    Properties are stored in the _props dict. Their value is either a
    python simple type, or an IProperty.

    Folder
    ------

    Children are accessed through the python mapping protocol.

    Children are stored through the _children attribute, which is a
    persistent subobject.
    """
    zope.interface.implements(IDocument)
    security = ClassSecurityInfo()

    # Derived __init__ must initialize _children
    _children = None

    def _getPath(self, first=False):
        if self.__parent__ is None:
            return (self.__name__,)
        else:
            return self.__parent__._getPath() + (self.__name__,)

    def __repr__(self):
        path = '/'.join(self._getPath(True))
        if not path:
            path = '/'
        return '<%s at %s>' % (self.__class__.__name__, path)

    def __nonzero__(self):
        # Always return true, even for empty folders
        return True

    # API

    security.declareProtected(View, 'getName')
    def getName(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self.__name__

    security.declareProtected(View, 'getUUID')
    def getUUID(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    security.declareProtected(View, 'getParent')
    def getParent(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        parent = self.__parent__
        if IChildren.providedBy(parent):
            parent = parent.__parent__
        elif parent is not None:
            print 'XXX doc parent is not IChildren but %r' % parent
        return parent

    ##### Children, delegating to _children

    security.declarePrivate('getChild')
    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if default is not _MARKER:
            return self._children.getChild(name, default)
        else:
            return self._children.getChild(name)

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children[name]

    security.declarePrivate('getChildren')
    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.getChildren()

    security.declareProtected(View, 'keys')
    def keys(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.keys()

    def __iter__(self):
        return iter(self._children)

    security.declareProtected(View, 'hasChild')
    def hasChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return name in self._children

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    security.declareProtected(View, 'hasChildren')
    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.hasChildren()

    security.declarePrivate('addChild')
    def addChild(self, name, type_name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.addChild(name, type_name)

    security.declareProtected(ModifyPortalContent, 'removeChild')
    def removeChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.removeChild(name)

    def __delitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        del self._children[name]

    security.declareProtected(ModifyPortalContent, 'clear')
    def clear(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children.clear()

    security.declareProtected(ModifyPortalContent, 'reorder')
    def reorder(self, names):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children.reorder(names)

    ##### Move / Copy

    security.declarePrivate('moveDocument')
    def moveDocument(self, destination, name):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    security.declarePrivate('copyDocument')
    def copyDocument(self, destination, name):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    ##### Properties, see ObjectBase

    ##### Misc

    def isReadOnly(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return False # XXX

    ##### Versioning

    security.declarePrivate('restore')
    def restore(self, versionName=''):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    security.declarePrivate('checkpoint')
    def checkpoint(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    security.declarePrivate('removeFrozen')
    def removeFrozen(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    def isCheckedOut(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return True # XXX

    ##### Search

    security.declarePrivate('locateUUID')
    def locateUUID(self, uuid):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    security.declarePrivate('searchProperty')
    def searchProperty(self, prop_name, value):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

InitializeClass(Document)


class Workspace(Document):
    """Root of a tree of documents.
    """
    zope.interface.implements(IWorkspace)


class Property(Persistent):
    """Base class for a Property.

    A property has its own individual persistence in the storage.
    """
    security = ClassSecurityInfo()

    __name__ = None
    __parent__ = None

    def getName(self):
        return self.__name__

    def getTypeName(self):
        raise NotImplementedError

    def _getPath(self, first=False):
        if self.__parent__ is None:
            return (self.__name__,)
        else:
            return self.__parent__._getPath() + (self.__name__,)

    def __repr__(self):
        path = '/'.join(self._getPath(True))
        return '<%s at %s>' % (self.__class__.__name__, path)

    security.declarePrivate('setDTO')
    def setDTO(self, value):
        raise NotImplementedError

    security.declarePrivate('getDTO')
    def getDTO(self):
        raise NotImplementedError

    @staticmethod
    def emptyDTO(iface, default):
        return default

InitializeClass(Property)


class ObjectProperty(ObjectBase, Property):
    """A complex type with fields based on a schema.
    """
    zope.interface.implements(IObjectProperty)

    def setDTO(self, value):
        """See `nuxeo.capsule.interfaces.IProperty`

        `value` is a mapping.
        """
        # XXX clear other props before?
        for k, v in value.iteritems():
            if k == '__name__':
                if v != self.getName():
                    raise ValueError("Mismatched names %s and %s" %(
                        v, self.getName()))
            else:
                self.setProperty(k, v)

    def getDTO(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a mapping.
        """
        value = {}
        for k, v in self._props.iteritems():
            if IProperty.providedBy(v):
                v = v.getDTO()
            value[k] = v
        # Name is stored so that setDTO can recognize list items
        value['__name__'] = self.getName()
        return value


class ContainerProperty(ContainerBase, ObjectProperty):
    """A complex type holding subobjects.
    """
    zope.interface.implements(IContainerProperty)

    def __init__(self, name, schema):
        ObjectProperty.__init__(self, name, schema)
        ContainerBase.__init__(self, name) # with ordering

    def setDTO(self, value):
        raise NotImplementedError

    def getDTO(self):
        raise NotImplementedError


class ListProperty(ContainerProperty):
    """A list of complex properties.

    Properties are stored as ordered subobjects.
    """
    zope.interface.implements(IListProperty)
    security = ClassSecurityInfo()

    def __init__(self, name, schema):
        ContainerProperty.__init__(self, name, schema)
        self._init()

    def _init(self):
        # This will be called in some cases by __setstate__
        schema = self.getSchema()
        types = schema['__setitem__'].getTaggedValue('precondition').types
        assert len(types) == 1, types
        value_schema = types[0]
        self._setValueSchema(value_schema)

    def _setValueSchema(self, schema):
        self._value_schema = schema

    security.declarePrivate('getValueSchema')
    def getValueSchema(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return self._value_schema

    security.declarePrivate('addValue')
    def addValue(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        raise NotImplementedError("Must be subclassed")

    def getDTO(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a list of python simple types.
        """
        l = []
        for ob in self:
            assert IProperty.providedBy(ob)
            v = ob.getDTO()
            l.append(v)
        return l

    def setDTO(self, values):
        """See `nuxeo.capsule.interfaces.IProperty`

        `value` is a list of python simple types.
        """
        # Find which items to keep
        kept = []
        for v in values:
            if not isinstance(v, dict):
                raise ValueError("Not a dict value: %r" % (v,))
            name = v.get('__name__')
            if name is not None:
                kept.append(name)
        # Remove items not kept
        for name in list(set(self._order) - set(kept)):
            self.removeChild(name)
        # Modify kept objects, or add new ones
        names = []
        for v in values:
            name = v.get('__name__')
            if name is not None:
                # XXX AT: creating a child with a known name is useful when
                # storing dict-like structure as a list.
                if self.hasChild(name):
                    ob = self.getChild(name)
                else:
                    ob = self.addValue(name=name)
            else:
                ob = self.addValue()
                name = ob.getName()
            names.append(name)
            ob.setDTO(v)
        # Set final order
        self.reorder(names)

    def __getitem__(self, index):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        k = self._order[index]
        return ContainerProperty.__getitem__(self, k)

    def __delitem__(self, index):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        k = self._order[index]
        self.removeChild(k)

    def __contains__(self, value):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return value in self._children

InitializeClass(ListProperty)


CONTENT_TYPE_MATCHER = re.compile('([^;\s]+)\s*(?:;\s*charset=([^\s]+)\s*)?$',
                                  re.I)


class ResourceProperty(ObjectProperty):
    """A resource property.

    Designed to hold a JCR nt:resource.
    """
    zope.interface.implements(IResourceProperty)

    def getTypeName(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return 'nt:resource' # otherwise it would use 'IResourceProperty'

    def setDTO(self, value):
        """See `nuxeo.capsule.interfaces.IProperty`

        `value` is a IResource or a Zope 2 File object.
        """
        if value is None:
            raise ValueError('None')
        if IResource.providedBy(value):
            blob = value.blob
            mime_type = value.mime_type
            encoding = value.encoding
            last_modified = value.last_modified
        else:
            # XXX zope 2 dependency...
            from OFS.Image import File
            if isinstance(value, File):
                blob = Blob(str(value.data))
                match = CONTENT_TYPE_MATCHER.match(value.content_type)
                if match is None:
                    logger.warning("Bad content-type %r" % value.content_type)
                    mime_type = None
                    encoding = None
                else:
                    mime_type, encoding = match.groups()
                t = value._p_mtime
                if t is not None:
                    last_modified = datetime(*time.gmtime(t)[:6])
                else:
                    last_modified = datetime(2000, 1, 1)
            else:
                raise TypeError(value)
        self.setProperty('jcr:data', blob)
        self.setProperty('jcr:mimeType', mime_type)
        self.setProperty('jcr:encoding', encoding)
        self.setProperty('jcr:lastModified', last_modified)

    def getDTO(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a IResource or None
        """
        blob = self.getProperty('jcr:data', None)
        if blob is None:
            return None
        mime_type = self.getProperty('jcr:mimeType', None)
        encoding = self.getProperty('jcr:encoding', None)
        last_modified = self.getProperty('jcr:lastModified', None)
        return Resource(blob, mime_type=mime_type, encoding=encoding,
                        last_modified=last_modified)

    @staticmethod
    def emptyDTO(iface, default):
        """Return a DTO for an empty property about to be created.
        """
        return None


##################################################
# Plain objects

class Resource(object):
    """A file object.

    This is the DTO of a ResourceProperty.

    A Resource cannot have a None blob.
    """
    zope.interface.implements(IResource)

    def __init__(self, blob, mime_type=None, encoding=None,
                 last_modified=None):
        if not isinstance(blob, Blob):
            print 'XXX', repr(blob)
            raise ValueError("%s data forbidden" % type(blob))
        self.blob = blob
        self.blob_len = len(blob)
        self.mime_type = mime_type
        self.encoding = encoding
        self.last_modified = last_modified

    def __len__(self):
        """See `nuxeo.capsule.interfaces.IResourceProperty`
        """
        return self.blob_len

    def __str__(self):
        """See `nuxeo.capsule.interfaces.IResourceProperty`
        """
        return str(self.blob)

    def open(self):
        """See `nuxeo.capsule.interfaces.IResourceProperty`
        """
        return StringIO(str(self.blob))

    def getFileUpload(self):
        """See `nuxeo.capsule.interfaces.IResourceProperty`

        Used by widgets. XXX should be lazy on the open/fetching!
        """
        # XXX zope 2 dependency...
        from ZPublisher.HTTPRequest import FileUpload
        from Products.CPSUtil.file import SimpleFieldStorage
        if self.encoding is None:
            content_type = self.mime_type
        else:
            content_type = '%s; charset=%s' % (self.mime_type, self.encoding)
        headers = {'content-type': content_type}
        filename = 'noname.bin'
        fs = SimpleFieldStorage(self.open(), filename, headers)
        return FileUpload(fs)

    def getContentType(self):
        if self.encoding is None:
            return self.mime_type
        else:
            return '%s; charset=%s' % (self.mime_type, self.encoding)


class Blob(object):
    """A binary blob.

    This is the DTO of a JCR Binary property.
    """
    zope.interface.implements(IBlob)

    def __init__(self, data):
        if not isinstance(data, str):
            raise ValueError("%s data forbidden" % type(data))
        self.data = data

    def __str__(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "<Blob at 0x%08x>" % id(self)


class Reference(object):
    """A reference to another object through its UUID.

    This is the DTO of a JCR Reference property.
    """
    zope.interface.implements(IReference)
    security = ClassSecurityInfo()

    security.declareObjectPublic()
    security.setDefaultAccess('allow')

    def __init__(self, uuid):
        self._target = uuid

    def getTargetUUID(self):
        """See `nuxeo.capsule.interfaces.IReference`.
        """
        return self._target

    def __repr__(self):
        return "Reference('%s')" % self._target

    def __cmp__(self, other):
        if not isinstance(other, Reference):
            return 1
        return cmp(self._target, other.getTargetUUID())

InitializeClass(Reference)
