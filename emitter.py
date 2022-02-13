import socket
import sys
from common import BaseHeader
from common import Client
from common import Communicator
from common import Parameter2BMessage

def usage():
    print("python emitter.py <serverIP>:<port> [exihibitorID]")

class Emitter(Client):

    def __init__(self, exhibitorID):
        super().__init__()
        self.myExhibitorID = exhibitorID    
    
    def _messageForHI(self):
        return {'type': Communicator.HI_MSG_ID, 'origin': self.myExhibitorID, 'destiny': Communicator.SERVID,
                 'sequence':self.sequence}
    
    def _clearAttr(self):
        super()._clearAttr()
        self.myExhibitorID = -1

    def readInputUntilMustClose(self):
        shouldStop = False
        while(not shouldStop):
            print("> ", end="")
            command = input()
            shouldStop = self._treatCommand(command)
        
        self.disconnectFromServer()
    
    def _treatCommand(self, command):
        shouldStop = False
        splitedCommand = command.split(" ")

        if splitedCommand[0] == "KILL":
            
            shouldStop = self._treatKillCommand()
        
        elif splitedCommand[0] == "MSG":
            self._treatMSGCommand(splitedCommand)
        
        elif splitedCommand[0] == "CREQ":
            self._treatCREQCommand(splitedCommand)
        
        elif splitedCommand[0] == "PLANET":
            self._treatPLANETCommand(splitedCommand)

        elif splitedCommand[0] == "PLANETLIST":
            self._treatPLANETLISTCommand(splitedCommand)
        else:
            print("< UNKNOWN COMMAND!")

        return shouldStop
    
    def _treatKillCommand(self):
        shouldStop = False
        sMsg = BaseHeader()
        message = {'type': Communicator.KILL_MSG_ID, 'origin': self.myID, 'destiny': self.myExhibitorID,
                     'sequence':self.sequence}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        self.sock.send(bMsg)
        self.sequence += 1

        data = self.sock.recv(1024)

        sMsg.fromBytes(data)

        if sMsg.type == 1:
            print("< OK")
            shouldStop = True
        
        return shouldStop

    def _treatMSGCommand(self, splitedCommand):
        
        if(len(splitedCommand) >= 3):
            sMsg = Parameter2BMessage()
            message = {}
            message['origin'] = self.myID
            message['destiny'] = int(splitedCommand[1])
            message['type'] = Communicator.MSG_MSG_ID
            message['sequence'] = self.sequence
            textMessage = " ".join(splitedCommand[2:])
            message['parameter'] = len(textMessage)
            message['message'] = textMessage

            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()
            self.sequence += 1
            
            self.sock.send(bMsg)
            
            #Rcv OK or ERROR
            data = self.sock.recv(1024)

            sMsg = BaseHeader()

            sMsg.fromBytes(data)

            self._printOKERRORMSGType(sMsg.type)
        else:
            print("< UNKNOWN COMMAND! Usage: MSG <destinyID> <message>")
    
    def _treatCREQCommand(self, splitedCommand):
        
        if len(splitedCommand) == 2:
            sMsg = BaseHeader()
            message = {'type': Communicator.CREQ_MSG_ID, 'origin': self.myID, 'destiny': int(splitedCommand[1]),
                         'sequence':self.sequence}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            self.sock.send(bMsg)
            self.sequence += 1

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            self._printOKERRORMSGType(sMsg.type)
        else:
            print("< UNKNOWN COMMAND! Usage: CREQ <destinyID>")
                
    def _treatPLANETCommand(self, splitedCommand):
        if len(splitedCommand) == 2:
            sMsg = BaseHeader()
            message = {'type': Communicator.PLANET_MSG_ID, 'origin': self.myID, 'destiny': int(splitedCommand[1]),
                         'sequence':self.sequence}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            self.sock.send(bMsg)
            self.sequence += 1

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            self._printOKERRORMSGType(sMsg.type)
        else:
            print("< UNKNOWN COMMAND! Usage: PLANET <destinyID>")
    
    def _treatPLANETLISTCommand(self, splitedCommand):
        if len(splitedCommand) == 1:
            sMsg = BaseHeader()
            message = {'type': Communicator.PLANETLIST_MSG_ID, 'origin': self.myID, 'destiny': Communicator.SERVID,
                         'sequence':self.sequence}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            self.sock.send(bMsg)
            self.sequence += 1

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            self._printOKERRORMSGType(sMsg.type)
        else:
            print("< UNKNOWN COMMAND! Usage: PLANETLIST")
    
    def _printOKERRORMSGType(self, type):
        if type == 1:
            print("> OK")
        elif type == 2:
            print("> ERROR! SOMETHING WENT WRONG!")


def runEmitter():

    exhibitorID = Communicator.NO_EXHIBITOR_ID
    if len(sys.argv) == 3:
        exhibitorID = int(sys.argv[2])

    emitter = Emitter(exhibitorID)
    serverAddr = sys.argv[1].split(":")

    if(len(serverAddr) == 2 and emitter.connectWith(serverAddr[0], int(serverAddr[1]))):
        emitter.readInputUntilMustClose()
    else:
        print("Program shutdown!")
        exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        usage()
        exit(1)
    
    runEmitter()