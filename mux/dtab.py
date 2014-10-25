class Dentry(object):
  def __init__(self, path, tree):
    self.path = path
    self.tree = tree

  def __eq__(self, other):
    return isinstance(other, Dentry) and self.path == other.path and self.tree == other.tree


class Dtab(object):
  @classmethod
  def empty(cls):
    return cls([])

  def __init__(self, entries):
    self.entries = entries

  def __eq__(self, other):
    # TODO(wickman) This should be made more sophisticated, obv.
    return isinstance(other, Dtab) and self.entries == other.entries

  def __iter__(self):
    return iter(self.entries)

  def __len__(self):
    return len(self.entries)
