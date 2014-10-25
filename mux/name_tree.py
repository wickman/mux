class NameTree(object):
  Neg = object()
  Fail = object()
  Empty = object()

  class Leaf(object):
    __slots__ = ('path',)

    def __init__(self, path):
      self.path = path

    def __eq__(self, other):
      return isinstance(other, NameTree.Leaf) and self.path == other.path

  class Alt(object):
    __slots__ = ('trees',)

    def __init__(self, *trees):
      self.trees = trees

    def __eq__(self, other):
      return isinstance(other, NameTree.Alt) and self.trees == other.trees

  class Union(object):
    __slots__ = ('trees',)

    def __init__(self, *trees):
      self.trees = trees

    def __eq__(self, other):
      return isinstance(other, NameTree.Union) and self.trees == other.trees
