import socket
import sys
from common import SimpleMessage
from common import BaseHeader
from common import Client
from common import Communicator

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
            print(">", end="")
            command = input()
            shouldStop = self._treatCommand(command)
        
        self.disconnectFromServer()
    
    def _treatCommand(self, command):
        shouldStop = False
        splitedCommand = command.split(" ")

        if splitedCommand[0] == "KILL":
            sMsg = BaseHeader()
            message = {'type': 4, 'origin': self.myID, 'destiny': self.myExhibitorID, 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            print('{}: sending {!r}'.format(self.sock.getsockname(), bMsg), file=sys.stderr)
            self.sock.send(bMsg)

            data = self.sock.recv(1024)

            sMsg.fromBytes(data)

            if sMsg.type == 1:
                shouldStop = True
        
        return shouldStop

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