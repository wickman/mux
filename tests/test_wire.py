from mux.wire import (
    Packet,
    Rdispatch,
    Rdrain,
    Rerr,
    Rping,
    Rreq,
    Tdiscarded,
    Tdispatch,
    Tdrain,
    Tlease,
    Tping,
    Treq,
)

import pytest


SHORT_MAX = 2 ** 24 - 1


def test_tlease():
  pass


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_tdiscarded(tag):
  msg = Tdiscarded(tag, 'horfgorf')
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag
  assert msg.why == msg2.why


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rerr(tag):
  msg = Rerr(tag, 'morfgorf')
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag
  assert msg.error == msg2.error


def test_rping():
  pass


def test_tping():
  pass


def test_rdrain():
  pass


def test_tdrain():
  pass


def test_rdispatch():
  pass


def test_tdispatch():
  pass


def test_treq():
  pass


def test_rreq():
  pass
