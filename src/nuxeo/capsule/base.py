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
from nuxeo.capsule.interfaces import IContainerBase
from nuxeo.capsule.interfaces import IDocument
from nuxeo.capsule.interfaces import IWorkspace
from nuxeo.capsule.interfaces import IChildren
from nuxeo.capsule.interfaces import IProperty
from nuxeo.capsule.interfaces import IObjectProperty
from nuxeo.capsule.interfaces import IContainerProperty
from nuxeo.capsule.interfaces import IListProperty
from nuxeo.capsule.interfaces import IBinaryProperty
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

    __parent__ = None
    _lazy = None
    _missing = None

    def __init__(self, name):
        self.__name__ = name
        self._children = {}
        self._order = [] # ordered XXX

    def _getPath(self, first=False):
        ppath = self.__parent__._getPath()
        return ppath + (self.__name__,)

    def __repr__(self):
        path = '/'.join(self._getPath(True))
        return '<%s at %s>' % (self.__class__.__name__, path)

    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        try:
            return self._children[name]
        except KeyError:
            if default is not _MARKER:
                return default
            raise

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children[name]

    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return iter(self)

    def __iter__(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if self._order is None:
            return self._children.itervalues()
        else:
            return (self._children[k] for k in self._order)

    def hasChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return name in self._children

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return bool(self._children)

    def addChild(self, name, type_name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        raise NotImplementedError("Must be subclassed")

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

    def clear(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children = {}
        if self._order is not None:
            self._order = []

    def reorder(self, names):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        if self._order is None:
            raise TypeError("Unordered container")
        if set(names) != set(self._order):
            raise ValueError("Names mismatch (%s to %s)" %
                             (self._order, names))
        self._order = list(names)


class Children(ContainerBase):
    """Holder of children nodes.
    """
    zope.interface.implements(IChildren)

    def __init__(self, name, schema=None):
        assert name == 'ecm:children', name
        ContainerBase.__init__(self, 'ecm:children')

    def getName(self):
        return self.__name__

    def getTypeName(self):
        """See `nuxeo.capsule.interfaces.IChildren`
        """
        raise NotImplementedError

    def _getPath(self, first=False):
        ppath = self.__parent__._getPath()
        if first:
            return ppath + (self.__name__,)
        else:
            return ppath


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
        parent = self.__parent__
        if IChildren.providedBy(parent):
            parent = parent.__parent__
        elif parent is not None:
            print 'XXX doc parent is not IChildren but %r' % parent
        return parent

    ##### Children, delegating to _children

    def getChild(self, name, default=_MARKER):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.getChild(name, default)

    def __getitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children[name]

    def getChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.getChildren()

    def __iter__(self):
        return iter(self._children)

    def hasChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return name in self._children

    def __contains__(self, name):
        return name in self._children

    def __len__(self):
        return len(self._children)

    def hasChildren(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.hasChildren()

    def addChild(self, name, type_name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.addChild(name, type_name)

    def removeChild(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        return self._children.removeChild(name)

    def __delitem__(self, name):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        del self._children[name]

    def clear(self):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children.clear()

    def reorder(self, names):
        """See `nuxeo.capsule.interfaces.IContainerBase`
        """
        self._children.reorder(names)

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

    def getName(self):
        return self.__name__

    def getTypeName(self):
        raise NotImplementedError

    def _getPath(self, first=False):
        return self.__parent__._getPath() + (self.__name__,)

    def __repr__(self):
        path = '/'.join(self._getPath(True))
        return '<%s at %s>' % (self.__class__.__name__, path)

    def setPythonValue(self, value):
        raise NotImplementedError

    def getPythonValue(self):
        raise NotImplementedError


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
            if k != '__name__':
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


class ContainerProperty(ContainerBase, ObjectProperty):
    """A complex type holding subobjects.
    """
    zope.interface.implements(IContainerProperty)

    def __init__(self, name, schema):
        ObjectProperty.__init__(self, name, schema)
        ContainerBase.__init__(self, name) # with ordering

    def setPythonValue(self, value):
        raise NotImplementedError

    def getPythonValue(self):
        raise NotImplementedError


class ListProperty(ContainerProperty):
    """A list of complex properties.

    Properties are stored as ordered subobjects.
    """
    zope.interface.implements(IListProperty)

    def __init__(self, name, schema):
        ContainerProperty.__init__(self, name, schema)
        types = schema['__setitem__'].getTaggedValue('precondition').types
        assert len(types) == 1, types
        value_schema = types[0]
        self._setValueSchema(value_schema)

    def _setValueSchema(self, schema):
        self._value_schema = schema

    def getValueSchema(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        return self._value_schema

    def addValue(self):
        """See `nuxeo.capsule.interfaces.IListProperty`
        """
        raise NotImplementedError("Must be subclassed")

    def getPythonValue(self):
        """See `nuxeo.capsule.interfaces.IProperty`

        Returns a list of python simple types.
        """
        l = []
        for ob in self:
            assert IProperty.providedBy(ob)
            v = ob.getPythonValue()
            # Name is stored so that setPythonValue can recognize items
            v['__name__'] = ob.getName()
            l.append(v)
        return l

    def setPythonValue(self, values):
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
            del self[name]
        # Modify kept objects, or add new ones
        names = []
        for v in values:
            name = v.get('__name__')
            if name is not None:
                ob = self.getChild(name)
            else:
                ob = self.addValue()
                name = ob.getName()
                v['__name__'] = name
            names.append(name)
            ob.setPythonValue(v)
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
