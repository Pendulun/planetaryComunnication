import struct

class MessageEncoderDecoder():
    
    def decode(self, bytes):
        messageTypeBytes = str(struct.unpack('h', bytes[0:2])[0])
        messageOriginBytes = str(struct.unpack('h', bytes[2:4])[0])
        messageDestinyBytes = str(struct.unpack('h', bytes[4:6])[0])
        messageSequenceBytes = str(struct.unpack('h', bytes[6:8])[0])
        messageHeader = " ".join([messageTypeBytes, messageOriginBytes, messageDestinyBytes, messageSequenceBytes])

        return messageHeader


    def encode(self, message: dict):
        messageTypeBytes = struct.pack('h', message['type'])
        messageOriginBytes = struct.pack('h', message['origin'])
        messageDestinyBytes = struct.pack('h', message['destiny'])
        messageSequenceBytes = struct.pack('h', message['sequence'])

        messageHeader = b"".join([messageTypeBytes, messageOriginBytes, messageDestinyBytes, messageSequenceBytes])
        print(messageHeader)

        return messageHeader

class BaseHeader():

    def __init__(self):
        self.type = ""
        self.origin = ""
        self.destiny = ""
        self.sequence = ""
    
    def fromBytes(self, bytes):
        self.type = struct.unpack('H', bytes[0:2])[0]
        self.origin = struct.unpack('H', bytes[2:4])[0]
        self.destiny = struct.unpack('H', bytes[4:6])[0]
        self.sequence = struct.unpack('H', bytes[6:8])[0]

        return self.__str__()
    
    def __str__(self):
        return " ".join([str(self.type), str(self.origin), str(self.destiny), str(self.sequence)])
    
    def toBytes(self):
        messageTypeBytes = struct.pack('H', self.type)
        messageOriginBytes = struct.pack('H', self.origin)
        messageDestinyBytes = struct.pack('H', self.destiny)
        messageSequenceBytes = struct.pack('H', self.sequence)

        messageHeader = b"".join([messageTypeBytes, messageOriginBytes, messageDestinyBytes, messageSequenceBytes])

        return messageHeader

    def setAttr(self, message: dict):
        self.type = message['type']
        self.origin = message['origin']
        self.destiny = message['destiny']
        self.sequence = message['sequence']

class SimpleMessage():

    def __init__(self):
        self.header = BaseHeader()
        self.message = ""
    
    def fromBytes(self, bytes):
        self.header.fromBytes(bytes)
        #self.message = str(struct.unpack('s', bytes[8:-1])[0])
        self.message = bytes[8:].decode()

    def __str__(self):
        return " ".join([self.header.__str__(), str(self.message)])
    
    def toBytes(self):
        #messageBytes = struct.pack('s', self.message)
        messageBytes = self.message.encode()

        completeMessage = b"".join([self.header.toBytes(), messageBytes])

        return completeMessage

    def setAttr(self, message: dict):
        self.header.setAttr(message)
        self.message = message['message']

class Parameter2BMessage():

    def __init__(self):
        self.header = BaseHeader()
        self.message = ""
        self.parameter = ""
    
    def fromBytes(self, bytes):
        self.header.fromBytes(bytes)
        self.parameter = str(struct.unpack('H', bytes[8:10])[0])
        self.message = bytes[10:].decode()

    def __str__(self):
        return " ".join([self.header.__str__(), str(self.parameter), str(self.message)])
    
    def toBytes(self):
        messageBytes = self.message.encode()
        parameterBytes = struct.pack('H', self.parameter)

        completeMessage = b"".join([self.header.toBytes(), parameterBytes, messageBytes])

        return completeMessage

    def setAttr(self, message: dict):
        self.header.setAttr(message)
        self.message = message['message']
        self.parameter = message['parameter']