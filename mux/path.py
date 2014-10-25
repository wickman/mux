class Path(object):
  @classmethod
  def empty(cls):
    return cls()

  def __init__(self, *components):
    self.components = components

  def __iter__(self):
    return iter(self.components)

  def __eq__(self, other):
    return isinstance(other, Path) and self.components == other.components
