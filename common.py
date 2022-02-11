import struct
import socket
import sys

class Communicator():
    SERVID = (2**16) - 1

class Client(Communicator):
    def __init__(self):
        self.myID = -1
        self.sock = -1
        self.connected = False
        self.planet = ""
    
    def _clearAttr(self):
        self.myID = -1
        self.sock = -1
        self.connected = False
        self.planet = ""
    
    def _shutdownWithError(self, errorMsg):
        print(f"Error: {errorMsg}")
        print("Shutting connection!", self.sock.getsockname(), file=sys.stderr)
        self.sock.close()
        self._clearAttr()
    
    def connectWith(self, serverIP, serverPort):
        server_address = (serverIP, serverPort)
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        print('connecting to {} port {}'.format(*server_address), file=sys.stderr)

        try:
            self.sock.connect(server_address)
        except:
            print("Connection failed!")
            return False
        
        self.connected = True
        
        if(self.checkForHI()):
            print(f"MY ID: {self.myID}")
            #ORIGIN
            self.planet = input("WRITE ORIGIN PLANET:\n> ")
            if(self.sendOrigin()):
                return True
            else:
                self._shutdownWithError("Send ORIGIN Failed!")
                return False
        else:
            self._shutdownWithError("Send HI Failed!")
            return False
        
        return True
    
    def checkForHI(self):
        #Enviar mensagem HI
        sMsg = BaseHeader()
        message = self._messageForHI()
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        print('{}: sending {!r}'.format(self.sock.getsockname(), bMsg), file=sys.stderr)
        self.sock.send(bMsg)

        #Receber resposta
        data = self.sock.recv(1024)
        sMsg.fromBytes(data)
        print('{}: received {}'.format(self.sock.getsockname(), data), file=sys.stderr)
        if(sMsg.type == 1):
            self.myID = sMsg.destiny
            return True
        else:
            return False
    
    def _messageForHI(self):
        raise NotImplementedError
    
    def sendOrigin(self):
        #Enviar mensagem HI
        sMsg = Parameter2BMessage()
        message = {'type': 3, 'origin': 0, 'destiny': 0, 'sequence':0, 'parameter': len(self.planet), 'message': self.planet}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        print('{}: sending {!r}'.format(self.sock.getsockname(), bMsg), file=sys.stderr)
        self.sock.send(bMsg)

        #Receber resposta
        data = self.sock.recv(1024)
        sMsg = BaseHeader()
        sMsg.fromBytes(data)
        print('{}: received {}'.format(self.sock.getsockname(), data), file=sys.stderr)
        if(sMsg.type == 1):
            return True
        else:
            return False
        
    def disconnectFromServer(self):
        print("Disconnecting from server!")
        self.sock.close()
        self._clearAttr()



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
    """
    A Message that contains only the base headers
    """

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
    """"
    A Message that contains the base headers and a message to be sent along with it
    """

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
    """"
    A Message that contains the base headers, a parameter of 2 bytes and a message to be sent along with it
    """

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