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


def test_tlease():
  pass


def test_tdiscarded():
  msg = Tdiscarded(31337, 'horfgorf')
  msg2 = Packet.decode(msg.encode())
  assert msg.tag == msg2.tag
  assert msg.why == msg2.why


def test_rerr():
  pass


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
