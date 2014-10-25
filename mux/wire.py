import struct

from .dtab import Dtab


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
  @classmethod
  def decode_string(cls, fmt, width, buf):
    if len(buf) < width:
      raise ValueError('Buffer too small to contain string.')

    length, = struct.unpack(fmt, buf[0:width])

    if len(buf) < width + length:
      raise ValueError('Buffer is truncated (expected string length %d)' % length)

    return length + width, buf[width:length + width].decode('utf-8')

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

    length, = struct.unpack('>I', buf[0:4])

    if len(buf) < 4 + length:
      raise ValueError('Buffer is truncated (expected packet length %d)' % length)

    return length + 4, Packet.decode(buf[4:length + 4])

  @classmethod
  def encode_context(cls, key, value):
    raw_key = key.encode('utf-8')
    raw_value = value.encode('utf-8')

    return b''.join([
        struct.pack('>H', len(raw_key)),
        raw_key,
        struct.pack('>H', len(raw_value)),
        raw_value,
    ])

  @classmethod
  def encode_contexts(cls, contexts):
    return struct.pack('>H', len(contexts)) + b''.join(
        cls.encode_context(k, v) for (k, v) in contexts)

  @classmethod
  def decode_context(cls, body):
    key_len, = struct.unpack('>H', body[0:2])
    key = body[2:key_len + 2].decode('utf-8')
    value_len, = struct.unpack('>H', body[key_len + 2:key_len + 4])
    value = body[key_len + 4:key_len + 4 + value_len].decode('utf-8')
    return key_len + value_len + 4, (key, value)

  @classmethod
  def decode_contexts(cls, body):
    num_contexts, = struct.unpack('>H', body[0:2])
    contexts = []

    offset = 2
    for _ in range(num_contexts):
      consumed, (k, v) = cls.decode_context(body[offset:])
      offset += consumed
      contexts.append((k, v))

    return offset, contexts


class Packet(object):
  IMPLS = {}

  @classmethod
  def decode(cls, buf):
    if not isinstance(buf, bytearray):
      raise TypeError('Packet.decode requires buffer of type bytearray.')

    if len(buf) < 4:
      raise ValueError('Buffer insufficient size for message.')

    typ = buf[0]

    # twos compliment conversion
    if 0 <= typ < 128:
      pass
    elif 128 <= typ < 256:
      typ -= 256
    else:
      raise ValueError('Invalid message type: %s' % typ)

    tag, = struct.unpack('>I', b'\x00' + buf[1:4])

    impl = cls.IMPLS.get(typ)

    if impl is None:
      raise ValueError('Unknown Tmessage (%d) 0x%x with tag 0x%x' % (typ, typ, tag))

    return impl.decode_body(tag, buf[4:])

  @classmethod
  def decode_body(cls, tag, body):
    raise NotImplemented

  @classmethod
  def register(cls, typ, impl):
    cls.IMPLS[typ] = impl

  def __init__(self, tag):
    self.tag = tag

  def encode_header(self, message_type):
    return bytearray().join([
        struct.pack('b', message_type),
        struct.pack('>I', self.tag)[1:]
    ])

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

  @classmethod
  def decode_kv(cls, kv):
    key = kv[0]
    value_len = kv[1]
    return value_len + 2, (key, kv[2:value_len + 2])

  @classmethod
  def decode_kvs(cls, body):
    offset = 1
    kvs = {}

    for kv in range(body[0]):
      consumed, (key, val) = cls.decode_kv(body[offset:])
      offset += consumed
      kvs[key] = val

    return offset, kvs

  @classmethod
  def decode_body(cls, tag, body):
    consumed, kvs = cls.decode_kvs(body)

    trace_id = kvs.get(cls.TRACE_ID)
    if trace_id:
      trace_id = TraceId.decode(trace_id)

    trace_flag = kvs.get(cls.TRACE_FLAG)
    if trace_flag:
      trace_flag = TraceFlag.decode(trace_flag)

    return cls(tag, body[consumed:], trace_id=trace_id, trace_flag=trace_flag)

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

    return bytearray().join([
        self.encode_header(Message.T_REQ),
        self.encode_kvs(kvs),
        self.body
    ])


class Rreq(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    status = body[0]

    if status not in (Status.OK, Status.ERROR, Status.NACK):
      raise ValueError('Got an unknown status type: 0x%x' % status)

    return cls(tag, status, body[1:])

  def __init__(self, tag, status, body):
    super(Rreq, self).__init__(tag)
    self.status = status
    self.body = body

  def encode(self):
    return bytearray().join([
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
  @classmethod
  def decode_body(cls, tag, body):
    consumed_contexts, contexts = Fragments.decode_contexts(body)
    consumed_dest, dest = Fragments.decode_s2(body[consumed_contexts:])
    consumed_dtab, dtab = Fragments.decode_contexts(body[consumed_contexts + consumed_dest:])
    body = body[consumed_contexts + consumed_dest + consumed_dtab:]
    return cls(tag, contexts, dest, Dtab(dtab), body)

  def __init__(self, tag, contexts, dest, dtab, body):
    super(Tdispatch, self).__init__(tag)

    if not isinstance(body, (bytearray, bytes)):
      raise TypeError('body must be of type bytes or a bytearray.')

    self.contexts, self.dest, self.dtab, self.body = tuple(contexts), dest, dtab, body

  def encode(self):
    return bytearray().join([
        self.encode_header(Message.T_DISPATCH),
        Fragments.encode_contexts(self.contexts),
        Fragments.encode_s2(self.dest),
        Fragments.encode_contexts(self.dtab),
        self.body,
    ])


class Rdispatch(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    status = body[0]

    if status not in (Status.OK, Status.ERROR, Status.NACK):
      raise ValueError('Got an unknown status type: 0x%x' % status)

    consumed, contexts = Fragments.decode_contexts(body[1:])
    body = body[1 + consumed:]

    return cls(tag, status, contexts, body)

  def __init__(self, tag, status, contexts, body):
    super(Rdispatch, self).__init__(tag)

    if not isinstance(body, (bytearray, bytes)):
      raise TypeError('body must be of type bytes or a bytearray.')

    self.status, self.contexts, self.body = status, tuple(contexts), body

  def encode(self):
    return bytearray().join([
        self.encode_header(Message.R_DISPATCH),
        struct.pack('B', self.status),
        Fragments.encode_contexts(self.contexts),
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
    super(RdispatchNack, self).__init__(tag, Status.NACK, contexts, b'')


class Tdrain(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    if body:
      raise ValueError('Tdrain expects empty body.')
    return cls(tag)

  def __init__(self, tag):
    super(Tdrain, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.T_DRAIN)


class Rdrain(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    if body:
      raise ValueError('Rdrain expects empty body.')
    return cls(tag)

  def __init__(self, tag):
    super(Rdrain, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.R_DRAIN)


class Tping(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    if body:
      raise ValueError('Tping expects empty body.')
    return cls(tag)

  def __init__(self, tag):
    super(Tping, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.T_PING)


class Rping(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    if body:
      raise ValueError('Rping expects empty body.')
    return cls(tag)

  def __init__(self, tag):
    super(Rping, self).__init__(tag)

  def encode(self):
    return self.encode_header(Message.R_PING)


class Rerr(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    return cls(tag, body.decode('utf-8'))

  def __init__(self, tag, error):
    super(Rerr, self).__init__(tag)
    self.error = error

  def encode(self):
    return self.encode_header(Message.R_ERR) + self.error.encode('utf-8')


class Tdiscarded(Packet):
  @classmethod
  def decode_body(cls, tag, body):
    return cls(tag, body.decode('utf-8'))

  def __init__(self, tag, why):
    super(Tdiscarded, self).__init__(tag)
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
    return bytearray().join([
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
