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
        return {'type': Communicator.HI_MSG_ID, 'origin': self.myExhibitorID, 'destiny': Communicator.SERVID, 'sequence':0}
    
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
            print("< INVALID COMMAND!")

        return shouldStop
    
    def _treatKillCommand(self):
        shouldStop = False
        sMsg = BaseHeader()
        message = {'type': Communicator.KILL_MSG_ID, 'origin': self.myID, 'destiny': self.myExhibitorID, 'sequence':0}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        #print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
        self.sock.send(bMsg)

        data = self.sock.recv(1024)

        sMsg.fromBytes(data)

        if sMsg.type == 1:
            shouldStop = True
        
        return shouldStop

    def _treatMSGCommand(self, splitedCommand):
        
        if(len(splitedCommand) >= 3):
            sMsg = Parameter2BMessage()
            message = {}
            message['origin'] = self.myID
            message['destiny'] = int(splitedCommand[1])
            message['type'] = Communicator.MSG_MSG_ID
            message['sequence'] = 0
            textMessage = " ".join(splitedCommand[2:])
            message['parameter'] = len(textMessage)
            message['message'] = textMessage

            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            #print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            
            self.sock.send(bMsg)
            
            #Rcv OK or ERROR
            data = self.sock.recv(1024)

            sMsg = BaseHeader()

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                print("> OK")
            elif sMsg.type == 2:
                print("> ERROR! SOMETHING WENT WRONG!")
    
    def _treatCREQCommand(self, splitedCommand):
        
        if len(splitedCommand) == 2:
            sMsg = BaseHeader()
            message = {'type': Communicator.CREQ_MSG_ID, 'origin': self.myID, 'destiny': int(splitedCommand[1]), 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            #print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            self.sock.send(bMsg)

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                print("> OK")
            elif sMsg.type == 2:
                print("> ERROR! SOMETHING WENT WRONG!")
                
    def _treatPLANETCommand(self, splitedCommand):
        if len(splitedCommand) == 2:
            sMsg = BaseHeader()
            message = {'type': Communicator.PLANET_MSG_ID, 'origin': self.myID, 'destiny': int(splitedCommand[1]), 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            #print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            self.sock.send(bMsg)

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                print("> OK")
            elif sMsg.type == 2:
                print("> ERROR! SOMETHING WENT WRONG!")
    
    def _treatPLANETLISTCommand(self, splitedCommand):
        if len(splitedCommand) == 1:
            sMsg = BaseHeader()
            message = {'type': Communicator.PLANETLIST_MSG_ID, 'origin': self.myID, 'destiny': Communicator.SERVID, 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            #print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            self.sock.send(bMsg)

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                print("> OK")
            elif sMsg.type == 2:
                print("> ERROR! SOMETHING WENT WRONG!")


def runEmitter():

    exhibitorID = Communicator.NO_EXHIBITOR_ID
    if len(sys.argv) == 3:
        exhibitorID = int(sys.argv[2])

    emitter = Emitter(exhibitorID)
    serverAddr = sys.argv[1].split(":")

    if(len(serverAddr) == 2 and emitter.connectWith(serverAddr[0], int(serverAddr[1]))):
        print("Se conectou!")
        emitter.readInputUntilMustClose()
    else:
        print("Program shutdown!")
        exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        usage()
        exit(1)
    
    runEmitter()