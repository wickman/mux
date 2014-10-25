from mux.parsers import parse_path
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
