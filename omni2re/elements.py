""" omniture.elements """
# encoding: utf-8

from copy import copy

from .utils import AddressableList, wrap


class Value(object):
    """ Omniture value """
    def __init__(self, title, vid, parent, extra=None):
        self.title = title
        self.vid = vid
        self.parent = parent
        self.properties = {'id': vid}
        if extra is None:
            extra = {}

        for k, i in extra.items():
            setattr(self, k, i)

    @classmethod
    def list(cls, name, items, parent, title='title', vid='id'):
        """ list values """
        values = [cls(item[title], item[vid], parent, item) for item in items]
        return AddressableList(values, name)

    def __repr__(self):
        return "<{title}: {id} in {parent}>".format(**self.__dict__)

    def copy(self):
        """ copy value """
        value = self.__class__(self.title, self.vid, self.parent)
        value.properties = copy(self.properties)
        return value

    def serialize(self):
        """ serialize value """
        return self.properties

    def __str__(self):
        return self.title


class Element(Value):
    """ Omniture element """
    def range(self, *vargs):
        i = len(vargs)
        if i == 1:
            start = 0
            stop = vargs[0]
        elif i == 2:
            start, stop = vargs

        top = stop - start

        element = self.copy()
        element.properties['startingWith'] = str(start)
        element.properties['top'] = str(top)

        return element

    def search(self, keywords, etype='AND'):
        etype = etype.upper()

        types = ['AND', 'OR', 'NOT']
        if etype not in types:
            raise ValueError("Search type should be one of: " + ", ".join(types))

        element = self.copy()
        element.properties['search'] = {
            'type': etype,
            'keywords': wrap(keywords),
        }
        return element

    def select(self, keys):
        element = self.copy()
        element.properties['selected'] = wrap(keys)
        return element


class Segment(Element):
    """ define segment as an Element """
    pass
