from mux.wire import (
    Packet,
    RdispatchError,
    RdispatchNack,
    RdispatchOk,
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


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_tlease(tag):
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


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rping(tag):
  msg = Rping(tag)
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_tping(tag):
  msg = Tping(tag)
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rdrain(tag):
  msg = Rdrain(tag)
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_tdrain(tag):
  msg = Tdrain(tag)
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rdispatch(tag):
  def assert_equiv(msg1, msg2):
    assert msg1.tag == msg2.tag
    assert msg1.status == msg2.status
    assert msg1.contexts == msg2.contexts
    assert msg1.body == msg2.body

  for contexts in [(), (('foo', 'bar'),), (('foo', 'bar'), ('bork', 'bonk'))]:
    for body in ['', 'baz']:
      msg = RdispatchOk(tag, contexts, body.encode('utf-8'))
      msg2 = Packet.decode(msg.encode())
      assert_equiv(msg, msg2)

      msg = RdispatchError(tag, contexts, body.encode('utf-8'))
      msg2 = Packet.decode(msg.encode())
      assert_equiv(msg, msg2)

      msg = RdispatchNack(tag, contexts)
      msg2 = Packet.decode(msg.encode())
      assert_equiv(msg, msg2)


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_tdispatch(tag):
  for contexts in [(), (('foo', 'bar'),), (('foo', 'bar'), ('bork', 'bonk'))]:
    for body in ['', 'baz']:
      for dest in ['/wat', '/x/y/z']:
        msg = Tdispatch(tag, contexts, dest, (), body)
        msg2 = Packet.decode(msg.encode())
        assert msg.tag == msg2.tag
        assert msg.dest == msg2.dest
        assert msg.contexts == msg2.contexts
        assert msg.dtab == msg2.dtab
        assert msg.body == msg2.body


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_treq(tag):
  pass


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rreq(tag):
  pass
