from .dtab import Dtab, Dentry
from .name_tree import NameTree
from .path import Path


class Buffer(object):
  @classmethod
  def wrap(cls, buf):
    if isinstance(buf, cls):
      return buf
    else:
      return cls(buf)

  def __init__(self, buf):
    self.buf = buf
    self.index = 0

  def peek(self):
    if self.at_end():
      return None
    return self.buf[self.index]

  def next(self):
    self.index += 1

  def maybe_eat(self, char):
    if self.peek() != char:
      return False
    self.next()
    return True

  def eat(self, char):
    if not self.maybe_eat(char):
      raise ValueError('Unexpected character %s' % self.peek())

  def eat_whitespace(self):
    while not self.at_end() and self.peek().isspace():
      self.next()

  def at_end(self):
    return self.index >= len(self.buf)


def char_range(start, end):
  return frozenset(chr(v) for v in range(ord(start), ord(end) + 1))


class Patterns(object):
  SHOWABLE_CHARS = frozenset.union(
      char_range('0', '9'),
      char_range('A', 'Z'),
      char_range('a', 'z'),
      frozenset(['_', ':', '.', '#', '$', '%', '-']),
  )

  @classmethod
  def is_showable(cls, ch):
    return ch in cls.SHOWABLE_CHARS

  @classmethod
  def is_label_char(cls, ch):
    return cls.is_showable(ch) or ch == '\\'


def parse_hex(buf):
  ch = buf.peek()
  buf.next()
  return int(ch, 16)


def parse_label(string):
  buf = Buffer.wrap(string)
  label = ''

  while True:
    ch = buf.peek()

    if Patterns.is_showable(ch):
      label += ch
      buf.next()
    elif ch == '\\':
      buf.next()
      buf.eat('x')
      fst = parse_hex(buf)
      snd = parse_hex(buf)
      label += chr(fst * 16 + snd)
    else:
      raise ValueError('Unknown character: %s' % ch)

    if not Patterns.is_label_char(buf.peek()):
      return label


def parse_path(string):
  buf = Buffer.wrap(string)
  buf.eat_whitespace()
  buf.eat('/')

  if not Patterns.is_label_char(buf.peek()):
    return Path.empty()

  labels = []

  while True:
    labels.append(parse_label(buf))
    if not buf.maybe_eat('/'):
      break

  return Path(labels)


def parse_dentry(string):
  buf = Buffer.wrap(string)
  path = parse_path(buf)
  buf.eat_whitespace()
  buf.eat('=')
  buf.eat('>')
  tree = parse_tree(buf)
  return Dentry(path, tree)


def parse_dtab(string):
  buf = Buffer.wrap(string)
  dentries = []

  while True:
    buf.eat_whitespace()
    if not buf.at_end():
      dentries.append(parse_dentry(buf))
      buf.eat_whitespace()
    if not buf.maybe_eat(';'):
      break

  return Dtab(dentries)


def parse_tree1(string):
  buf = Buffer.wrap(string)

  trees = []

  while True:
    trees.append(parse_simple(buf))
    buf.eat_whitespace()
    if not buf.maybe_eat('&'):
      break

  if len(trees) > 1:
    return NameTree.Union(*trees)
  else:
    return trees[0]


def parse_simple(string):
  buf = Buffer.wrap(string)

  buf.eat_whitespace()
  ch = buf.peek()

  if ch == '(':
    buf.next()
    tree = parse_tree(buf)
    buf.eat_whitespace()
    buf.eat(')')
    return tree
  elif ch == '/':
    return NameTree.Leaf(parse_path(buf))
  elif ch == '!':
    buf.next()
    return NameTree.Fail
  elif ch == '~':
    buf.next()
    return NameTree.Neg
  elif ch == '$':
    buf.next()
    return NameTree.Empty
  else:
    raise ValueError('Failed to parse NameTree.')


def parse_tree(string):
  buf = Buffer.wrap(string)

  trees = []

  while True:
    trees.append(parse_tree1(buf))
    buf.eat_whitespace()
    if not buf.maybe_eat('|'):
      break

  if len(trees) > 1:
    return NameTree.Alt(*trees)
  else:
    return trees[0]
