from mux.wire import (
    Packet,
    RdispatchError,
    RdispatchNack,
    RdispatchOk,
    Rdrain,
    Rerr,
    Rping,
    RreqError,
    RreqNack,
    RreqOk,
    Tdiscarded,
    Tdispatch,
    Tdrain,
    Tlease,
    Tping,
    TraceFlag,
    TraceId,
    Treq,
)

import pytest


SHORT_MAX = 2 ** 24 - 1
ULL_MAX = 2 ** 64 - 1


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
@pytest.mark.randomize(('length', 'int'), min_num=0, max_num=ULL_MAX)
def test_tlease(tag, length):
  msg = Tlease(tag, 1, length)
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag
  assert msg.unit == msg2.unit
  assert msg.length == msg2.length

  with pytest.raises(ValueError):
    Tlease(tag, 0, length)


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

      msg = RdispatchError(tag, contexts, body)
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
        msg = Tdispatch(tag, contexts, dest, (), body.encode('utf-8'))
        msg2 = Packet.decode(msg.encode())
        assert msg.tag == msg2.tag
        assert msg.dest == msg2.dest
        assert msg.contexts == msg2.contexts
        assert msg.dtab == msg2.dtab
        assert msg.body == msg2.body


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_treq(tag):
  def assert_equiv(msg1, msg2):
    assert msg1.tag == msg2.tag
    assert msg1.body == msg2.body
    assert msg1.trace_id == msg2.trace_id
    assert msg1.trace_flag == msg2.trace_flag

  for body in (b'', b'foo'):
    # w/o traces
    msg = Treq(tag, body)
    msg2 = Packet.decode(msg.encode())
    assert_equiv(msg, msg2)

    # w/ traces
    trace_id = TraceId(1, 2, 3)
    msg = Treq(tag, body, trace_id=trace_id)
    msg2 = Packet.decode(msg.encode())
    assert_equiv(msg, msg2)

    for trace_flag in TraceFlag.default(), TraceFlag.debug():
      msg = Treq(tag, body, trace_id=trace_id, trace_flag=trace_flag)
      msg2 = Packet.decode(msg.encode())
      assert_equiv(msg, msg2)

    with pytest.raises(ValueError):
      # must specify trace_id
      Treq(tag, body, trace_flag=TraceFlag.debug())


@pytest.mark.randomize(('tag', 'int'), min_num=0, max_num=SHORT_MAX)
def test_rreq(tag):
  def assert_equiv(msg1, msg2):
    assert msg1.tag == msg2.tag
    assert msg1.status == msg2.status
    assert msg1.body == msg2.body

  for body in ('', 'baz'):
    msg = RreqOk(tag, body.encode('utf-8'))
    msg2 = Packet.decode(msg.encode())
    assert_equiv(msg, msg2)

    msg = RreqError(tag, body)
    msg2 = Packet.decode(msg.encode())
    assert_equiv(msg, msg2)

    msg = RreqNack(tag)
    msg2 = Packet.decode(msg.encode())
    assert_equiv(msg, msg2)

