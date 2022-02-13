import struct
import socket
import sys

class Communicator():
    SERVID = (2**16) - 1
    NO_EXHIBITOR_ID = 1
    ALL_EXHIBITORS = 0
    ALL_CLIENTS = 0
    EXHIBITOR_HI_MSG_ID = 0

    OK_MSG_ID = 1
    ERROR_MSG_ID = 2
    HI_MSG_ID = 3
    KILL_MSG_ID = 4
    MSG_MSG_ID = 5
    CREQ_MSG_ID = 6
    CLIST_MSG_ID = 7
    ORIGIN_MSG_ID = 8
    PLANET_MSG_ID = 9
    PLANETLIST_MSG_ID = 10

class Client(Communicator):
    def __init__(self):
        self.myID = -1
        self.sock = -1
        self.connected = False
        self.planet = ""
        self.sequence = 0
    
    def _clearAttr(self):
        self.myID = -1
        self.sock = -1
        self.connected = False
        self.planet = ""
        self.sequence = 0
    
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
            print(f"MY ID< {self.myID}")
            #ORIGIN
            self.planet = input("WRITE ORIGIN PLANET> ")
            if(self.sendOrigin()):
                return True
            else:
                self._shutdownWithError("< Send ORIGIN Failed!")
                return False
        else:
            self._shutdownWithError("< Send HI Failed!")
            return False
    
    def checkForHI(self):

        sMsg = BaseHeader()
        message = self._messageForHI()
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        self.sock.send(bMsg)
        self.sequence += 1

        #Receber resposta
        data = self.sock.recv(1024)
        sMsg.fromBytes(data)

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
        message = {'type': Communicator.ORIGIN_MSG_ID, 'origin': self.myID, 'destiny': Communicator.SERVID,
                     'sequence':self.sequence, 'parameter': len(self.planet), 'message': self.planet}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        self.sock.send(bMsg)
        self.sequence += 1

        #Receber resposta
        data = self.sock.recv(1024)
        sMsg = BaseHeader()
        sMsg.fromBytes(data)

        if(sMsg.type == 1):
            print("< OK")
            return True
        else:
            print("< Send ORIGIN failed!")
            return False
        
    def disconnectFromServer(self):
        print("Disconnecting from server!")
        self.sock.close()
        self._clearAttr()

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