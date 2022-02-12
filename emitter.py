from lib2to3.pytree import Base
import socket
import sys
from common import SimpleMessage
from common import BaseHeader
from common import Client
from common import Communicator
from common import Parameter2BMessage

def usage():
    print("python emitter.py <serverIP> <port> <exihibitorID>")

class Emitter(Client):

    def __init__(self, exhibitorID):
        super().__init__()
        self.myExhibitorID = exhibitorID    
    
    def _messageForHI(self):
        return {'type': 3, 'origin': self.myExhibitorID, 'destiny': Communicator.SERVID, 'sequence':0}
    
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

        return shouldStop
    
    def _treatKillCommand(self):
        shouldStop = False
        sMsg = BaseHeader()
        message = {'type': 4, 'origin': self.myID, 'destiny': self.myExhibitorID, 'sequence':0}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
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
            message['type'] = 5
            message['sequence'] = 0
            textMessage = " ".join(splitedCommand[2:])
            message['parameter'] = len(textMessage)
            message['message'] = textMessage

            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            
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
            message = {'type': 6, 'origin': self.myID, 'destiny': int(splitedCommand[1]), 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
            self.sock.send(bMsg)

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                print("> OK")
            elif sMsg.type == 2:
                print("> ERROR! SOMETHING WENT WRONG!")

def runEmitter():

    emitter = Emitter(int(sys.argv[3]))

    if(emitter.connectWith(sys.argv[1], int(sys.argv[2]))):
        print("Se conectou!")
        emitter.readInputUntilMustClose()
    else:
        print("Program shutdown!")
        exit(1)

    
if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
        exit(1)
    
    runEmitter()