from mux.dtab import Dtab, Dentry
from mux.name_tree import NameTree
from mux.parsers import (
    parse_dentry,
    parse_dtab,
    parse_path,
    parse_tree,
)
from mux.path import Path

import pytest


def test_parse_path():
  assert parse_path('/') == Path.empty()
  assert parse_path('  /foo/bar  ') == Path(['foo', 'bar'])
  assert parse_path('/\\x66\\x6f\\x6F') == Path(['foo'])

  # "/{}" -- How does this pass scala tests?
  for path in ("", "/foo/bar/", "/\\?", "/\\x?", "/\\x0?"):
    with pytest.raises(ValueError):
      parse_path(path)


def test_parse_name_tree():
  assert parse_tree("! | ~ | $") == NameTree.Alt(NameTree.Fail, NameTree.Neg, NameTree.Empty)
  assert parse_tree("/foo/bar") == NameTree.Leaf(Path(["foo", "bar"]))
  assert parse_tree("  /foo & /bar  ") == NameTree.Union(
      NameTree.Leaf(Path(["foo"])),
      NameTree.Leaf(Path(["bar"])))
  assert parse_tree("  /foo | /bar  ") == NameTree.Alt(
      NameTree.Leaf(Path(["foo"])),
      NameTree.Leaf(Path(["bar"])))
  assert parse_tree("/foo & /bar | /bar & /baz") == NameTree.Alt(
      NameTree.Union(
          NameTree.Leaf(Path(["foo"])),
          NameTree.Leaf(Path(["bar"]))),
      NameTree.Union(
          NameTree.Leaf(Path(["bar"])),
          NameTree.Leaf(Path(["baz"]))))

  for name_tree in ('', '#', '/foo &'):
    with pytest.raises(ValueError):
      parse_tree(name_tree)


def test_parse_dentry():
  assert parse_dentry("/=>!") == Dentry(Path.empty(), NameTree.Fail)
  assert parse_dentry("/ => !") == Dentry(Path.empty(), NameTree.Fail)

  with pytest.raises(ValueError):
    parse_dentry("/&!")


def test_parse_dtab():
  # TODO(wickman) Implement Dtab.empty() etc
  assert parse_dtab("") == Dtab()
  assert parse_dtab("  /=>!  ") == Dtab([Dentry(Path.empty(), NameTree.Fail)])
  assert parse_dtab("/=>!;") == Dtab([Dentry(Path.empty(), NameTree.Fail)])
  assert parse_dtab("/=>!;/foo=>/bar") == Dtab([
      Dentry(Path.empty(), NameTree.Fail),
      Dentry(Path(["foo"]), NameTree.Leaf(Path(["bar"])))
  ])
