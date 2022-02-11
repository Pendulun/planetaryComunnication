import select
import socket
import sys
import queue
import struct
import random
from common import SimpleMessage
from common import BaseHeader
from common import Communicator
from common import Parameter2BMessage

def usage():
    print("Usage: python server.py <port>")

class Server(Communicator):
    MINEXIID = 2**12
    MAXEXID = (2**13)-1
    MINEMID = 1
    MAXEMID = (2**12) - 1

    def __init__(self):
        self.sock = -1
        self.sequence = 0
        self.exihibitors = []
        self.emitters = []
        self.clientsInfo = {}
        self.takenExhibitors = []
        self.outputs = []
        self.inputs = []
        self.message_queues = {}
    
    def generateExihibitorId(self):
        exId = random.randint(Server.MINEXIID, Server.MAXEXID)
        while exId in self.exihibitors:
            exId = random.randint(Server.MINEXIID, Server.MAXEXID)
        
        return exId
    
    def generateEmitterId(self):
        emId = random.randint(Server.MINEMID, Server.MAXEMID)
        while emId in self.emitters:
            emId = random.randint(Server.MINEMID, Server.MAXEMID)
        
        return emId

    def createServerSocket(self, port):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)

        # Bind the socket to the port
        server_address = (socket.gethostname(), port)

        print('starting up on {} port {}'.format(*server_address),
            file=sys.stderr)
        self.sock.bind(server_address)

        print(self.sock.getsockname())
    
    def _closeConnectionWith(self, socket):
        print(f'  closing {socket.getpeername()}', file=sys.stderr)
        # Stop listening for input on the connection
        if socket in self.outputs:
            self.outputs.remove(socket)
        self.inputs.remove(socket)
        socket.close()

        # Remove message queue
        del self.message_queues[socket]

    def run(self):

        if not self.sock:
            return

        # Listen for incoming connections
        self.sock.listen(5)

        # Sockets from which we expect to read
        self.inputs = [self.sock]

        # Sockets to which we expect to write
        self.outputs = []

        # Outgoing message queues (socket:Queue)
        self.message_queues = {}

        client_ids = {}

        while self.inputs:

            # Wait for at least one of the sockets to be
            # ready for processing
            print('waiting for the next event', file=sys.stderr)
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            
            # Handle inputs
            for s in readable:

                if s is self.sock:
                    # A "readable" socket is ready to accept a connection
                    connection, client_address = s.accept()
                    print('  connection from', client_address, file=sys.stderr)
                    connection.setblocking(0)
                    self.inputs.append(connection)

                    # Give the connection a queue for data
                    # we want to send
                    print(f"Criou entrada no message queue para {connection}")
                    self.message_queues[connection] = queue.Queue()
                else:
                    data = s.recv(1024)
                    if data:
                        #print('Received {} from {}'.format(data, s.getpeername()), file=sys.stderr,)
                    
                        responses = self.treatMessage(data, s)
                        
                        for (socket, message) in responses.items():
                            self.message_queues[socket].put(message)
                            if socket not in self.outputs:
                                self.outputs.append(socket)
                                
                    else:
                        # Interpret empty result as closed connection
                        self._closeConnectionWith(s)

            # Handle outputs
            for s in writable:
                try:
                    next_msg = self.message_queues[s].get_nowait()
                except queue.Empty:
                    # No messages waiting so stop checking
                    # for writability.
                    print('  ', s.getpeername(), 'queue empty', file=sys.stderr)
                    self.outputs.remove(s)
                else:
                    msgType = struct.unpack("H", next_msg[0:2])[0]

                    shouldCloseConnection = False
                    if msgType in [1, 4, 8]:
                        sMsg = BaseHeader()
                        sMsg.fromBytes(next_msg)
                        print('  sending {} to {}'.format(sMsg, s.getpeername()), file=sys.stderr)
                    
                        if msgType == 4:
                            #Its a KILL for a exhibitor
                            exhibitorId = sMsg.destiny
                            self.exihibitors.remove(exhibitorId)
                            del self.clientsInfo[exhibitorId]
                            shouldCloseConnection = True
                            
                    if(self.message_queues[s].empty()):
                        self.outputs.remove(s)
                    
                    s.send(next_msg)
                    if(shouldCloseConnection):
                        self._closeConnectionWith(s)

            # Handle "exceptional conditions"
            for s in exceptional:
                print('exception condition on', s.getpeername(), file=sys.stderr)
                # Stop listening for input on the connection
                self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()

                # Remove message queue
                del self.message_queues[s]
    
    def treatMessage(self, bytesMessage, inSocket):

        messageType = struct.unpack("H", bytesMessage[0:2])[0]

        responses = {}
        
        if  messageType == 3:
            
            responses = self._treatHIMessage(bytesMessage, inSocket)
        
        elif messageType == 4:

            responses = self._treatKillMessage(bytesMessage, inSocket)
        
        elif messageType == 8:

            responses = self._treatOriginMessage(bytesMessage, inSocket)

        return responses                                   
        
    def _isEmissorHIMsg(self, message: BaseHeader):
        return message.origin >= Server.MINEXIID and message.origin < Server.MAXEXID
    
    def _isExhibitorHIMsg(self, message: BaseHeader):
        return message.origin == 0
    
    def _exhibitorExists(self, exhibitorId):
        return exhibitorId in self.exihibitors
    
    def _treatHIMessage(self, bMessage, inSocket):
        self.sequence += 1
        
        responses = {}

        inMessage = BaseHeader()
        inMessage.fromBytes(bMessage)
        print('Received {} from {}'.format(inMessage, inSocket.getpeername()), file=sys.stderr,)
        
        if self._isEmissorHIMsg(inMessage):
            responseMessage = ""
            if(self._exhibitorExists(inMessage.origin)):
                newId = self.generateEmitterId()
                print(f"GENERATED EMITTER ID: {newId}")
                self.emitters.append(newId)
                self.takenExhibitors.append(inMessage.origin)
                responseMessage = self.getOKMessageFor(newId)
                self.clientsInfo[newId] = {'socket': inSocket, 'exhibitor': inMessage.origin} 
            else:
                responseMessage = self.getErrorMessageFor(0)
            
            responses[inSocket] = responseMessage
            
        elif self._isExhibitorHIMsg(inMessage):
            #É um exibidor
            newId = self.generateExihibitorId()
            print(f"GENERATED EXHIBITOR ID: {newId}")
            self.exihibitors.append(newId)
            
            responseMessage = self.getOKMessageFor(newId)

            self.clientsInfo[newId] = {'socket': inSocket}

            responses[inSocket] = responseMessage
        
        return responses
    
    def _treatKillMessage(self, bytesMessage, inSocket):
        self.sequence += 1
        responses = {}

        inMessage = BaseHeader()
        inMessage.fromBytes(bytesMessage)
        print('Received {} from {}'.format(inMessage, inSocket.getpeername()), file=sys.stderr,)
        if self._exhibitorExists(inMessage.destiny):
            print("Encontrou ID EXHIBIDOR")
            exhibitorSocket = self.clientsInfo[inMessage.destiny]['socket']

            message = {}
            message['origin'] = inMessage.origin
            message['destiny'] = inMessage.destiny
            message['type'] = 4
            message['sequence'] = self.sequence
            myMessage = BaseHeader()
            myMessage.setAttr(message)
            responseMessage = myMessage.toBytes()

            responses[exhibitorSocket] = responseMessage
        else:
            print("NÃO Encontrou ID EXHIBIDOR")
        
        responses[inSocket] = self.getOKMessageFor(inMessage.origin)
        
        return responses
    
    def _treatOriginMessage(self, bytesMessage, inSocket):
        self.sequence += 1

        responses = {}

        inMessage = Parameter2BMessage()
        inMessage.fromBytes(bytesMessage)
        print('Received {} from {}'.format(inMessage, inSocket.getpeername()), file=sys.stderr,)

        self.clientsInfo[inMessage.header.origin]['Planet'] = inMessage.message
        responseMessage = self.getOKMessageFor(inMessage.header.origin)

        responses[inSocket] = responseMessage

        return responses

    def getErrorMessageFor(self, clientID):
        inMessage = BaseHeader()
        message = {}
        message['origin'] = Communicator.SERVID
        message['destiny'] = clientID
        message['type'] = 4
        message['sequence'] = self.sequence
        inMessage.setAttr(message)
        return inMessage.toBytes()
    
    def getOKMessageFor(self, clientID):
        inMessage = BaseHeader()
        message = {}
        message['origin'] = Communicator.SERVID
        message['destiny'] = clientID
        message['type'] = 1
        message['sequence'] = self.sequence
        inMessage.setAttr(message)
        return inMessage.toBytes()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        exit(1)
    
    server = Server()
    server.createServerSocket(int(sys.argv[1]))
    server.run()
