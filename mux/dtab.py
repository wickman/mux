class Dentry(object):
  def __init__(self, path, tree):
    self.path = path
    self.tree = tree

  def __eq__(self, other):
    return isinstance(other, Dentry) and self.path == other.path and self.tree == other.tree


class Dtab(tuple):
  pass
