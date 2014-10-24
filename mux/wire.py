import struct


class Status(object):
  OK = 0
  ERROR = 1
  NACK = 2


class Message(object):
  # Application messages
  T_REQ = 1
  R_REQ = -T_REQ

  T_DISPATCH = 2
  R_DISPATCH = -T_DISPATCH

  # Control messages
  T_DRAIN = 64
  R_DRAIN = -T_DRAIN

  T_PING = 65
  R_PING = -T_PING

  T_DISCARDED = 66
  T_LEASE = 67

  R_ERR = -128


class TraceId(object):
  __slots__ = ('span_id', 'parent_id', 'trace_id')

  def __init__(self, span_id, parent_id, trace_id):
    self.span_id, self.parent_id, self.trace_id = span_id, parent_id, trace_id

  def encode(self):
    return struct.pack('>QQQ', self.span_id, self.parent_id, self.trace_id)


class TraceFlag(object):
  @classmethod
  def debug(cls):
    return cls(1)

  @classmethod
  def default(cls):
    return cls(0)

  def __init__(self, flags):
    self.flags = flags

  def encode(self):
    return struct.pack('B', self.flags)


class Fragments(object):
  MAX_STRING_LENGTH = 2**24

  @classmethod
  def decode_string(cls, fmt, width, buf):
    if len(buf) < width:
      raise ValueError('Buffer too small to contain string.')

    length = struct.unpack(fmt, buf[0:width])

    if len(buf) < width + length:
      raise ValueError('Buffer is truncated (expected string length %d)' % length)

    return length + width, buf[width:length+width].decode('utf-8')

  @classmethod
  def decode_s1(cls, buf):
    return cls.decode_string('B', 1, buf)

  @classmethod
  def decode_s2(cls, buf):
    return cls.decode_string('>H', 2, buf)

  @classmethod
  def decode_s4(cls, buf):
    return cls.decode_string('>I', 4, buf)

  @classmethod
  def encode_string(cls, fmt, string):
    encoded_string = string.encode('utf-8')

    try:
      return struct.pack(fmt, len(encoded_string)) + encoded_string
    except struct.error as e:
      raise ValueError('Failed to serialize string: %s' % e)

  @classmethod
  def encode_s1(cls, string):
    return cls.encode_string('b', string)

  @classmethod
  def encode_s2(cls, string):
    return cls.encode_string('>H', string)

  @classmethod
  def encode_s4(cls, string):
    return cls.encode_string('>I', string)

  @classmethod
  def decode_packet(cls, buf):
    if len(buf) < 4:
      raise ValueError('Buffer too small to contain packet.')

    length = struct.unpack('>I', buf[0:4])

    if len(buf) < 4 + length:
      raise ValueError('Buffer is truncated (expected packet length %d)' % length)

    return length + 4, Packet.decode(buf[4:length+4])

  @classmethod
  def encode_context(cls, key, value):
    return b''.join([
      struct.pack('>H', len(key)),
      key,
      struct.pack('>H', len(value)),
      value,
    ])

  @classmethod
  def encode_contexts(cls, contexts):
    return struct.pack('>H', len(contexts)) + b''.join(
        self.encode_context(k, v) for (k, v) in contexts)


class Packet(object):
  IMPLS = {}

  @classmethod
  def decode(cls, buf):
    if len(buf) == 0:
      raise ValueError('Buffer should be nonzero size.')

    typ = struct.unpack('b', buf[0])
    impl = cls.IMPLS.get(typ)

    if impl is None:
      raise ValueError('Unknown Tmessage 0x%x' % typ)

    return impl.decode(buf)

  @classmethod
  def register(cls, typ, impl):
    cls.IMPLS[typ] = impl

  def __init__(self, tag):
    self.tag = tag

  def encode_header(self, message_type):
    return struct.pack('b', message_type) + struct.pack('>I', self.tag)[1:]

  def encode(self):
    raise NotImplemented


class Treq(Packet):
  TRACE_ID = 1
  TRACE_FLAG = 2

  @classmethod
  def encode_kv(cls, kv):
    return struct.pack('B', kv[0]) + struct.pack('B', len(kv[1])) + kv[1]

  @classmethod
  def encode_kvs(cls, kvs):
    return struct.pack('B', len(kvs)) + b''.join(cls.encode_kv(kv) for kv in kvs)

  def __init__(self, tag, body, trace_id=None, trace_flag=None):
    super(Treq, self).__init__(tag)
    self.body = body
    self.trace_id = trace_id
    self.trace_flag = trace_flag

    if self.trace_flag and not self.trace_id:
      raise ValueError('Cannot specify a trace_flag without a trace_id')

    if self.trace_id and not self.trace_flag:
      self.trace_flag = TraceFlag.default()

  def encode(self):
    if self.trace_id:
      kvs = [
        (self.TRACE_ID, self.trace_id.encode()),
        (self.TRACE_FLAG, self.trace_flag.encode()),
      ]
    else:
      kvs = []

    return b''.join([
      self.encode_header(Message.T_REQ),
      self.encode_kvs(kvs),
      self.body
    ])


class Rreq(Packet):
  def __init__(self, tag, status, body):
    super(Rreq, self).__init__(tag)
    self.status = status
    self.body = body

  def encode(self):
    return b''.join([
      self.encode_header(Message.R_REQ),
      struct.pack('B', self.status),
      self.body,
    ])


class RreqOk(Rreq):
  def __init__(self, tag, reply):
    super(RreqOk, self).__init__(tag, Status.OK, reply)


class RreqError(Rreq):
  def __init__(self, tag, error):
    super(RreqError, self).__init__(tag, Status.ERROR, error.encode('utf-8'))


class RreqNack(Rreq):
  def __init__(self, tag):
    super(RreqNack, self).__init__(tag, Status.NACK, b'')


class Tdispatch(Packet):
  def __init__(self, tag, contexts, dst, dtab, body):
    super(Tdispatch, self).__init__(tag)
    self.contexts, self.dst, self.dtab, self.body = contexts, dst, dtab, body

  def encode(self):
    return b''.join([
      self.encode_header(Message.T_DISPATCH),
      Fragment.encode_contexts(self.contexts),
      Fragment.encode_s2(self.dst),
      Fragment.encode_contexts(self.dtab),
      self.body,
    ])


class Rdispatch(Packet):
  def __init__(self, tag, status, contexts, body):
    super(Rdispatch, self).__init__(tag)
    self.status, self.contexts, self.body = status, contexts, body

  def encode(self):
    return b''.join([
      self.encode_header(Message.R_DISPATCH),
      struct.pack('B', self.status),
      Fragment.encode_contexts(self.contexts),
      self.body,
    ])


class RdispatchOk(Rdispatch):
  def __init__(self, tag, contexts, reply):
    super(RdispatchOk, self).__init__(tag, Status.OK, contexts, reply)


class RdispatchError(Rdispatch):
  def __init__(self, tag, contexts, error):
    super(RdispatchError, self).__init__(tag, Status.ERROR, contexts, error.encode('utf-8'))


class RdispatchNack(Rdispatch):
  def __init__(self, tag, contexts):
    super(RdispatchOk, self).__init__(tag, Status.NACK, contexts, b'')


class Tdrain(Packet):
  def __init__(self, tag):
    super(Tdrain, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.T_DRAIN)


class Rdrain(Packet):
  def __init__(self, tag):
    super(Rdrain, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.R_DRAIN)


class Tping(Packet):
  def __init__(self, tag):
    super(Tping, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.T_PING)


class Rping(Packet):
  def __init__(self, tag):
    super(Rping, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.R_PING)


class Rerr(Packet):
  def __init__(self, tag, error):
    super(Rerr, self).__init__(self.tag)
    self.error = error

  def encode(self):
    return self.encode_header(Message.R_ERR) + self.error.encode('utf-8')


class Tdiscarded(Packet):
  def __init__(self, tag, why):
    super(Tdiscarded, self).__init__(self.tag)
    self.why = why

  def encode(self):
    return self.encode_header(Message.T_DISCARDED) + self.why.encode('utf-8')


class Tlease(Packet):
  @classmethod
  def from_timestamp(cls, timestamp):
    pass

  @classmethod
  def from_amount(cls, duration):
    pass

  def __init__(self, tag, unit, length):
    super(Tlease, self).__init__(tag)
    self.unit, self.length = unit, length

  def encode(self):
    return b''.join([
        self.encode_header(Message.T_LEASE),
        struct.pack('B', self.unit),
        struct.pack('>Q', self.length)
    ])


Packet.register(Message.T_REQ, Treq)
Packet.register(Message.R_REQ, Rreq)
Packet.register(Message.T_DISPATCH, Tdispatch)
Packet.register(Message.R_DISPATCH, Rdispatch)
Packet.register(Message.T_DRAIN, Tdrain)
Packet.register(Message.R_DRAIN, Rdrain)
Packet.register(Message.T_PING, Tping)
Packet.register(Message.R_PING, Rping)
Packet.register(Message.T_DISCARDED, Tdiscarded)
Packet.register(Message.T_LEASE, Tlease)
Packet.register(Message.R_ERR, Rerr)
