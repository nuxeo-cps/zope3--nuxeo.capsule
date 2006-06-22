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

import Acquisition
from persistent import Persistent
from cStringIO import StringIO

import zope.interface
from nuxeo.capsule.interfaces import IObjectBase
from nuxeo.capsule.interfaces import IDocument
from nuxeo.capsule.interfaces import IWorkspace
from nuxeo.capsule.interfaces import IChildren
from nuxeo.capsule.interfaces import IProperty
from nuxeo.capsule.interfaces import IBinaryProperty
from nuxeo.capsule.interfaces import IListProperty
from nuxeo.capsule.interfaces import IObjectProperty
from nuxeo.capsule.interfaces import IReference

_MARKER = object()


class ObjectBase(Persistent):
    """A complex object with properties based on a schema.

    Properties are stored in the _props dict. Their value is either a
    python simple type, or an IProperty.
    """
    zope.interface.implements(IObjectBase)

    __parent__ = None

    def __init__(self, name, schema):
        self.__name__ = name
        self._setSchema(schema)
        self._props = {}

    def _setSchema(self, schema):
        self._schema = schema

    def getSchema(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self._schema

    def getTypeName(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self.getSchema().getName()

    def getProperties(self):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return self._props.copy()

    def getProperty(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        try:
            return self._props[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    def hasProperty(self, name):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        return name in self._props

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

    def XXX__getattr__(self, name):
        """See `nuxeo.capsule.interfaces.IObjectBase`
        """
        try:
            return self._props[name]
        except KeyError:
            raise AttributeError(name)


class Children(Persistent):
    """Holder of children nodes.

    Children all have distinct names, and can be ordered or not.

    Children are stored inside the _children attribute, which maps a
    unicode name to a IDocument

    For ordered folders, the _order list contains the ordered list of
    keys. For unordered folders, _order is None.

    For unordered folders, the children may be loaded lazily from the
    storage (because these folders can be big). In this case:

    - _lazy is a set storing the names of already loaded children,

    - _missing is a set storing the names of nonexistent children.

    If child loading is not lazy, _lazy and _missing are None.
    """
    zope.interface.implements(IChildren)

    __name__ = 'cps:children'
    _lazy = None
    _missing = None

    def __init__(self):
        self.__parent__ = None
        self._children = {}
        self._order = [] # ordered XXX

    def getName(self):
        return self.__name__

    def __repr__(self):
        if not self.__name__:
            return '<%s at />' % self.__class__.__name__
        path = []
        current = self
        while current is not None:
            path.append(current.getName())
            current = current.__parent__
        path.reverse()
        return '<%s at %s>' % (self.__class__.__name__, '/'.join(path))

    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        try:
            return self._children[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        return self._children[name]

    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        if self._order is None:
            return self._children.itervalues()
        else:
            return [self._children[k] for k in self._order]

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        return bool(self._children)

    def addChild(self, child):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        name = child.getName()
        if name in self._children:
            raise KeyError("Child %r already exists" % name)
        self._children[name] = child
        if self._order is not None:
            self._order.append(name)

    def removeChild(self, name):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        child = self._children[name]
        del self._children[name]
        if self._order is not None:
            self._order.remove(name)
        return child


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

    _children = None

    def __init__(self, name, schema):
        ObjectBase.__init__(self, name, schema)

    def __repr__(self):
        if not self.__name__:
            return '<%s at />' % self.__class__.__name__
        path = []
        current = self
        while current is not None:
            path.append(current.getName())
            current = current.__parent__
        path.reverse()
        return '<%s at %s>' % (self.__class__.__name__, '/'.join(path))

    def __nonzero__(self):
        # Always return true, even for empty folders
        return True

    # API

    def getName(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self.__name__

    def getUUID(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    def getParent(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self.__parent__

    ##### Children

    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self._children.getChild(name, default)

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self._children[name]

    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self._children.getChildren()

    def hasChild(self, name):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return name in self._children

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return self._children.hasChildren()

    def addChild(self, name, type_name):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    def removeChild(self, name):
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

    def checkout(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    def checkin(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        raise NotImplementedError

    def isCheckedOut(self):
        """See `nuxeo.capsule.interfaces.IDocument`
        """
        return True # XXX

    #
    # ZMI # XXX here for now, later in a Zope2-specific subclass
    #

    def getId(self):
        """Get the id of the object."""
        return self.getName()

    manage_main__roles__ = None # Public
    def manage_main(self, REQUEST=None, RESPONSE=None):
        """View object. XXX"""
        from cgi import escape
        res = ['<html>']

        res.append("<em>Internal:</em><br/>")
        for key in sorted(self.__dict__.keys()):
            if key in ('_children', '_order', '_props'):
                continue
            value = self.__dict__[key]
            ev = escape(repr(value))
            if key == '__parent__':
                ev = '<a href="../manage_main">%s</a>' % ev
            res.append('<strong>%s</strong>: %s<br/>'
                       % (escape(str(key)), ev))

        res.append("<br/><em>Properties:</em><br/>")
        for key, value in sorted(self.getProperties().items()):
            if IProperty.providedBy(value):
                value = value.getPythonValue()
            res.append('<strong>%s</strong>: %s<br/>' %
                       (escape(str(key)), escape(repr(value))))

        res.append("<br/><em>Children:</em><br/>")
        for value in self.getChildren():
            name = value.getName()
            href = './'+name # handle : in names
            ev = escape(repr(value))
            ev = '<a href="%s/manage_main">%s</a>' % (href, ev)
            res.append('<strong>%s</strong>: %s<br/>' %
                       (escape(str(name)), ev))
        res.append('</html>')
        return '\n'.join(res)


class Workspace(Document):
    """Root of a tree of documents.
    """
    zope.interface.implements(IWorkspace)


class Property(Persistent):
    """Base class for a Property.

    A property has its own individual persistence in the storage.
    """

    __name__ = None
    __parent__ = None
    #_value = None # XXX

    def getName(self):
        return self.__name__

    def __repr__(self):
        return '<%s %r of %r>' % (
            self.__class__.__name__, self.__name__, self.__parent__)

    def setPythonValue(self, value):
        raise NotImplementedError

    def getPythonValue(self):
        raise NotImplementedError


class BinaryProperty(Property):
    """A binary object (blob).
    """
    zope.interface.implements(IBinaryProperty)

    mime_type = None
    encoding = None

    def __init__(self, data, mime_type=None, encoding=None):
        if isinstance(data, unicode):
            raise ValueError('unicode data')
        self._value = data
        self._len = len(data)
        self.mime_type = mime_type
        self.encoding = encoding

    def open(self):
        """See `nuxeo.capsule.interfaces.IBinaryProperty`
        """
        return StringIO(self._value)

    def __len__(self):
        """See `nuxeo.capsule.interfaces.IBinaryProperty`
        """
        return self._len

    def __str__(self):
        """See `nuxeo.capsule.interfaces.IBinaryProperty`
        """
        return self._value


class ListProperty(Property):
    """A list of properties.
    """
    zope.interface.implements(IListProperty)

    def __init__(self, name, value_schema, values=None):
        self.__name__ = name
        self._setValueSchema(value_schema)
        self._values = list(values or ())

    def _setValueSchema(self, schema):
        self._value_schema = schema

    def getValueSchema(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return self._value_schema

    def _createItem(self):
        """Create one item for the list.
        """
        raise NotImplementedError("Must be subclassed")

    def getPythonValue(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a list of python simple types.
        """
        value = []
        for v in self._values:
            if IProperty.providedBy(v):
                v = v.getPythonValue()
            value.append(v)
        return value

    def setPythonValue(self, value):
        """See `nuxeo.capsule.interfaces.IProperty`

        `value` is a list of python simple types.
        """
        l = []
        for v in value:
            if isinstance(v, dict):
                item = self._createItem()
                item.setPythonValue(v)
                v = item
            l.append(v)
        self._values = l

    def addValue(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        ob = self._createItem()
        self._p_changed = True
        self._values.append(ob)
        return ob

    def __getitem__(self, index):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return self._values[index]

    def __len__(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return len(self._values)

    def __contains__(self, val):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return val in self._values

    def __iter__(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return iter(self._values)


class ObjectProperty(ObjectBase, Property):
    """A complex type with fields based on a schema.
    """
    zope.interface.implements(IObjectProperty)

    def setPythonValue(self, value):
        """See `nuxeo.capsule.interfaces.IProperty`

        `value` is a mapping.
        """
        # XXX clear other props before?
        for k, v in value.iteritems():
            self.setProperty(k, v)

    def getPythonValue(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a mapping.
        """
        value = {}
        for k, v in self._props.iteritems():
            if IProperty.providedBy(v):
                v = v.getPythonValue()
            value[k] = v
        return value


class Reference(object):
    """A reference to another object through its UUID.
    """
    zope.interface.implements(IReference)

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
