from .path import Path


class Buffer(object):
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


def parse_label(buf):
  label = ''

  while True:
    ch = buf.peek()

    if Patterns.is_showable(ch):
      print('showable: %s' % ch)
      label += ch
      buf.next()
    elif ch == '\\':
      print('slash: %s' % ch)
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
  buf = Buffer(string)

  buf.eat_whitespace()
  buf.eat('/')

  if not Patterns.is_label_char(buf.peek()):
    print('not label char: %s' % buf.peek())
    return Path.empty()

  labels = []

  while True:
    labels.append(parse_label(buf))
    if not buf.maybe_eat('/'):
      break

  return Path(labels)



def parse_dentry(string):
  pass


def parase_dtab(string):
  pass


