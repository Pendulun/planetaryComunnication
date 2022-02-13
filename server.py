import select
import socket
import sys

import queue
import struct
import random

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
    MAXLISTEN = 5

    def __init__(self):
        self.sock = -1
        self.sequence = 0
        self.exihibitors = []
        self.emitters = []

        self.clientsInfo = {}
        self.takenExhibitors = []
        self.idToSocketMap = {}
        self.socketToIdMap = {}

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
        server_address = ("", port)
        self.sock.bind(server_address)
        localIp = socket.gethostbyname(socket.gethostname())
        localname = socket.gethostname()
        print(f"Listening connections on {localname}/{localIp}/localhost on port {port}")
    
    def _closeConnectionWith(self, socket):
        print(f'closing {socket.getpeername()}', file=sys.stderr)
        # Stop listening for input on the connection
        if socket in self.outputs:
            self.outputs.remove(socket)
        self.inputs.remove(socket)

        if socket in self.socketToIdMap:

            clientId = self.socketToIdMap[socket]

            if clientId in self.exihibitors:
                self.exihibitors.remove(clientId)
                if clientId in self.takenExhibitors:
                    self.takenExhibitors.remove(clientId)

            elif clientId in self.emitters:
                self.emitters.remove(clientId)
            
            if clientId in self.idToSocketMap:
                del self.idToSocketMap[clientId]

            # Remove message queue
            if clientId in self.clientsInfo:
                del self.clientsInfo[clientId]
        
        if socket in self.message_queues:
            del self.message_queues[socket]
        
        if socket in self.socketToIdMap:
            del self.socketToIdMap[socket]
        
        socket.close()

    def run(self):

        if not self.sock:
            return

        # Listen for incoming connections
        self.sock.listen(Server.MAXLISTEN)

        # Sockets from which we expect to read
        self.inputs = [self.sock]

        # Sockets to which we expect to write
        self.outputs = []

        # Outgoing message queues (socket:Queue)
        self.message_queues = {}

        while self.inputs:

            # Wait for at least one of the sockets to be
            # ready for processing
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)
            
            # Handle inputs
            for s in readable:

                if s is self.sock:
                    # A "readable" socket is ready to accept a connection
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    self.inputs.append(connection)

                    # Give the connection a queue for data
                    # we want to send
                    self.message_queues[connection] = queue.Queue()
                else:
                    data = s.recv(1024)
                    if data:
                    
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
                    print(s.getpeername(), 'queue empty', file=sys.stderr)
                    self.outputs.remove(s)
                else:
                    msgType = struct.unpack("H", next_msg[0:2])[0]

                    shouldCloseConnection = False
                    
                    if msgType in [Communicator.OK_MSG_ID, Communicator.KILL_MSG_ID, Communicator.ORIGIN_MSG_ID]:
                        sMsg = BaseHeader()
                        sMsg.fromBytes(next_msg)
                    
                        if msgType == Communicator.KILL_MSG_ID:
                            #Server sending a KILL to a exhibitor
                            shouldCloseConnection = True
                            
                    elif msgType == Communicator.MSG_MSG_ID:
                        sMsg = Parameter2BMessage()
                        sMsg.fromBytes(next_msg)

                        print(f"Sending MSG from {sMsg.header.origin} to {sMsg.header.destiny}")
                    
                    if(self.message_queues[s].empty()):
                        self.outputs.remove(s)
                    
                    s.send(next_msg)
                    if(shouldCloseConnection):
                        self._closeConnectionWith(s)

            # Handle "exceptional conditions"
            for s in exceptional:
                print('exception condition on', s.getpeername(), file=sys.stderr)
                # Stop listening for input on the connection
                self._closeConnectionWith(s)
    
    def treatMessage(self, bytesMessage, inSocket):

        sMsg = BaseHeader()
        sMsg.fromBytes(bytesMessage)
        messageType = sMsg.type

        responses = {}
        
        if  messageType == Communicator.HI_MSG_ID:
            
            responses = self._treatHIMessage(bytesMessage, inSocket)
        
        else:
            messageOrigin = sMsg.origin

            if (self._checkOriginAuth(messageOrigin, inSocket)):

                if messageType == Communicator.OK_MSG_ID:
                    #OK Message
                    pass

                elif messageType == Communicator.KILL_MSG_ID:

                    responses = self._treatKillMessage(bytesMessage, inSocket)
                
                elif messageType == Communicator.MSG_MSG_ID:

                    responses = self._treatMSGMessage(bytesMessage, inSocket)
                
                elif messageType == Communicator.CREQ_MSG_ID:

                    responses = self._treatCREQMessage(bytesMessage, inSocket)
                
                elif messageType == Communicator.ORIGIN_MSG_ID:

                    responses = self._treatOriginMessage(bytesMessage, inSocket)
                
                elif messageType == Communicator.PLANET_MSG_ID:

                    responses = self._treatPlanetMessage(bytesMessage, inSocket)
                
                elif messageType == Communicator.PLANETLIST_MSG_ID:

                    responses = self._treatPlanetListMessage(bytesMessage, inSocket)

        return responses   

    def _checkOriginAuth(self, id, sock):
        return self.idToSocketMap[id] == sock                   
    
    def _idIsInEmitterRange(self, id):
        return id >= Server.MINEXIID and id < Server.MAXEXID

    def _isEmissorHIMsg(self, message: BaseHeader):
        return message.origin != Communicator.EXHIBITOR_HI_MSG_ID
    
    def _isExhibitorHIMsg(self, message: BaseHeader):
        return message.origin == Communicator.EXHIBITOR_HI_MSG_ID
    
    def _exhibitorExists(self, exhibitorId):
        return exhibitorId in self.exihibitors
    
    def _emitterExists(self, id):
        return id in self.emitters
    
    def _treatHIMessage(self, bMessage, inSocket):
        self.sequence += 1
        
        responses = {}

        inMessage = BaseHeader()
        inMessage.fromBytes(bMessage)
        print("received HI")

        if self._isEmissorHIMsg(inMessage):
            responseMessage = ""
            exhibitorExists = self._exhibitorExists(inMessage.origin)
            if(exhibitorExists or inMessage.origin == Communicator.NO_EXHIBITOR_ID):
                newId = self.generateEmitterId()
                self.idToSocketMap[newId] = inSocket
                self.emitters.append(newId)
                responseMessage = self.getOKMessageFor(newId)
                self.clientsInfo[newId] = {'socket': inSocket, 'exhibitor': inMessage.origin}
                self.socketToIdMap[inSocket] = newId
                if(exhibitorExists):
                    self.takenExhibitors.append(inMessage.origin)
            else:
                print(f"Error from {0}")
                responseMessage = self.getErrorMessageFor(0)
            
            responses[inSocket] = responseMessage
            
        elif self._isExhibitorHIMsg(inMessage):
            newId = self.generateExihibitorId()
            self.idToSocketMap[newId] = inSocket
            self.exihibitors.append(newId)
            
            responseMessage = self.getOKMessageFor(newId)

            self.clientsInfo[newId] = {'socket': inSocket}
            self.socketToIdMap[inSocket] = newId
            responses[inSocket] = responseMessage
        
        return responses
    
    def _treatKillMessage(self, bytesMessage, inSocket):
        self.sequence += 1
        responses = {}

        inMessage = BaseHeader()
        inMessage.fromBytes(bytesMessage)

        print(f"Received KILL from {inMessage.origin}")

        if self._exhibitorExists(inMessage.destiny):
            exhibitorSocket = self.clientsInfo[inMessage.destiny]['socket']

            message = {}
            message['origin'] = inMessage.origin
            message['destiny'] = inMessage.destiny
            message['type'] = Communicator.KILL_MSG_ID
            message['sequence'] = self.sequence
            myMessage = BaseHeader()
            myMessage.setAttr(message)
            responseMessage = myMessage.toBytes()

            responses[exhibitorSocket] = responseMessage
        
        del self.idToSocketMap[inMessage.origin]
        responses[inSocket] = self.getOKMessageFor(inMessage.origin)
        
        return responses
    
    def _treatOriginMessage(self, bytesMessage, inSocket):
        self.sequence += 1

        responses = {}

        inMessage = Parameter2BMessage()
        inMessage.fromBytes(bytesMessage)

        print(f"Received {inMessage.message} from {inMessage.header.origin}")

        self.clientsInfo[inMessage.header.origin]['planet'] = inMessage.message
        responseMessage = self.getOKMessageFor(inMessage.header.origin)

        responses[inSocket] = responseMessage

        return responses
    
    def _treatMSGMessage(self, bytesMessage, inSocket):
        self.sequence += 1

        responses = {}

        foundDestinyOfMessage = False

        inMessage = Parameter2BMessage()
        inMessage.fromBytes(bytesMessage)

        if inMessage.header.destiny == Communicator.ALL_EXHIBITORS:

            foundDestinyOfMessage = True

            for exID in self.exihibitors:
                exSocket = self.clientsInfo[exID]['socket']
                responses[exSocket] = bytesMessage

        elif (self._exhibitorExists(inMessage.header.destiny)):

            foundDestinyOfMessage = True
            exSocket = self.clientsInfo[inMessage.header.destiny]['socket']
            responses[exSocket] = bytesMessage
            
        elif (self._emitterExists(inMessage.header.destiny)):

            foundDestinyOfMessage = True
            emitterExhibitor = self.clientsInfo[inMessage.header.origin]['exhibitor']
            if emitterExhibitor in self.takenExhibitors:
                exSocket = self.clientsInfo[emitterExhibitor]['socket']
                responses[exSocket] = bytesMessage
        

        if (foundDestinyOfMessage):
            responses[inSocket] = self.getOKMessageFor(inMessage.header.origin)
        else:
            print(f"Error from {inMessage.origin}")
            responses[inSocket] = self.getErrorMessageFor(inMessage.header.origin)

        return responses


    def _treatCREQMessage(self, bytesMessage, inSocket):
        self.sequence += 1
        responses = {}
        foundDestinyOfMessage = False

        inMessage = BaseHeader()
        inMessage.fromBytes(bytesMessage)

        clientListString = " ".join([str(client) for client in self.getClientList()])
        numClients = len(self.getClientList())

        if inMessage.destiny == Communicator.ALL_CLIENTS:

            print(f"Received CREQ from {inMessage.origin} to ALL CLIENTS")

            foundDestinyOfMessage = True
            exhibitorsToBeSent = []

            #Messages for emitter's exhibitors
            for emitterID in self.emitters:

                emitterExhibitor = self.clientsInfo[emitterID]['exhibitor']

                if(emitterExhibitor != Communicator.NO_EXHIBITOR_ID):
                
                    exhibitorsToBeSent.append(emitterExhibitor)

                    exSocket = self.clientsInfo[emitterExhibitor]['socket']
                    bMsg = self.getCLISTMessage(emitterExhibitor, numClients, clientListString)
                    responses[exSocket] = bMsg

            #Messages for leftover exhibitors so we send only one msg to a exhibitor
            for exID in self.exihibitors:
                if exID not in exhibitorsToBeSent:

                    exSocket = self.clientsInfo[exID]['socket']
                    bMsg = self.getCLISTMessage(exID, numClients, clientListString)
                    responses[exSocket] = bMsg

        elif (self._exhibitorExists(inMessage.destiny)):

            print(f"Received CREQ from {inMessage.origin} to {inMessage.destiny}")

            foundDestinyOfMessage = True

            exSocket = self.clientsInfo[inMessage.destiny]['socket']
            bMsg = self.getCLISTMessage(inMessage.destiny, numClients, clientListString) 
            responses[exSocket] = bMsg
            
        elif (self._emitterExists(inMessage.destiny)):

            print(f"Received CREQ from {inMessage.origin} to {inMessage.destiny}")

            foundDestinyOfMessage = True

            emitterExhibitor = self.clientsInfo[inMessage.origin]['exhibitor']
            if emitterExhibitor in self.takenExhibitors:
                exSocket = self.clientsInfo[emitterExhibitor]['socket']
                bMsg = self.getCLISTMessage(emitterExhibitor, numClients, clientListString) 
                responses[exSocket] = bMsg

        if (foundDestinyOfMessage):
            responses[inSocket] = self.getOKMessageFor(inMessage.origin)
        else:
            print(f"Error from {inMessage.origin}")
            responses[inSocket] = self.getErrorMessageFor(inMessage.origin)

        return responses
    
    def _treatPlanetMessage(self, bytesMessage, inSocket):
        self.sequence += 1
        responses = {}
        foundDestinyOfMessage = False
        
        inMessage = BaseHeader()
        inMessage.fromBytes(bytesMessage)

        emitterExhibitor = self.clientsInfo[inMessage.origin]['exhibitor']

        if (emitterExhibitor != Communicator.NO_EXHIBITOR_ID and inMessage.destiny in self.clientsInfo):

            print(f"Received PLANET from {inMessage.origin} to {inMessage.destiny}")

            foundDestinyOfMessage = True

            emitterExhibitor = self.clientsInfo[inMessage.origin]['exhibitor']
            exSocket = self.clientsInfo[emitterExhibitor]['socket']

            destinyPlanet = self.clientsInfo[inMessage.destiny]['planet']

            bMsg = self.getPLANETMessage(inMessage.origin, inMessage.destiny, inMessage.sequence, destinyPlanet)
            responses[exSocket] = bMsg

        if (foundDestinyOfMessage):
            responses[inSocket] = self.getOKMessageFor(inMessage.origin)
        else:
            print(f"Error from {inMessage.origin}")
            responses[inSocket] = self.getErrorMessageFor(inMessage.origin)

        return responses
        
    def _treatPlanetListMessage(self, bytesMessage, inSocket):
        self.sequence += 1
        responses = {}
        foundDestinyOfMessage = False
        
        inMessage = BaseHeader()
        inMessage.fromBytes(bytesMessage)

        if  self.clientsInfo[inMessage.origin]["exhibitor"] != Communicator.NO_EXHIBITOR_ID:
            foundDestinyOfMessage = True

            emitterExhibitor = self.clientsInfo[inMessage.origin]['exhibitor']
            exSocket = self.clientsInfo[emitterExhibitor]['socket']
            print(f"Received PLANETLIST from {inMessage.origin} to {emitterExhibitor}")
            
            planetListString = " ".join(list(self._getSetOfClientPlanets()))

            bMsg = self.getPLANETLISTMessage(emitterExhibitor, planetListString)
            responses[exSocket] = bMsg
            

        if (foundDestinyOfMessage):
            responses[inSocket] = self.getOKMessageFor(inMessage.origin)
        else:
            print(f"Error from {inMessage.origin}")
            responses[inSocket] = self.getErrorMessageFor(inMessage.origin)

        return responses
    
    def _getSetOfClientPlanets(self):
        planetSet = set()

        for (_, clientInfo) in self.clientsInfo.items():
            clientPlanet = clientInfo['planet']
            planetSet.add(clientPlanet)
        
        return planetSet
    
    def getClientList(self):
        return self.clientsInfo.keys()
    
    def getCLISTMessage(self, destiny, parameter, message):
        sMsg = Parameter2BMessage()

        mensagem = {}
        mensagem['type'] = Communicator.CLIST_MSG_ID
        mensagem['origin'] = Communicator.SERVID
        mensagem['destiny'] = destiny
        mensagem['sequence'] = self.sequence
        mensagem['parameter'] = parameter
        mensagem['message'] = message

        sMsg.setAttr(mensagem)
        return sMsg.toBytes()
    
    def getPLANETMessage(self, origin, destiny, sequence, planet):
        sMsg = Parameter2BMessage()

        message = {}
        message['type'] = Communicator.PLANET_MSG_ID
        message['origin'] = origin
        message['destiny'] = destiny
        message['sequence'] = sequence
        message['parameter'] = len(planet)
        message['message'] = planet
        sMsg.setAttr(message)

        return sMsg.toBytes()
    
    def getPLANETLISTMessage(self, exhibitorID, planetList):
        sMsg = Parameter2BMessage()

        message = {}
        message['type'] = Communicator.PLANETLIST_MSG_ID
        message['origin'] = Communicator.SERVID
        message['destiny'] = exhibitorID
        message['sequence'] = self.sequence
        message['parameter'] = len(planetList)
        message['message'] = planetList
        sMsg.setAttr(message)

        return sMsg.toBytes()

    def getErrorMessageFor(self, clientID):
        inMessage = BaseHeader()
        message = {}
        message['origin'] = Communicator.SERVID
        message['destiny'] = clientID
        message['type'] = Communicator.ERROR_MSG_ID
        message['sequence'] = self.sequence
        inMessage.setAttr(message)
        return inMessage.toBytes()
    
    def getOKMessageFor(self, clientID):
        inMessage = BaseHeader()
        message = {}
        message['origin'] = Communicator.SERVID
        message['destiny'] = clientID
        message['type'] = Communicator.OK_MSG_ID
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