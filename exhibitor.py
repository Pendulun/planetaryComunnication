import socket
import sys
import struct
from common import SimpleMessage
from common import BaseHeader
from common import Client
from common import Communicator
from common import Parameter2BMessage

def usage():
    print("python emitter.py <serverIP> <port>")

class Exhibitor(Client):

    def __init__(self):
        super().__init__()
    
    def _messageForHI(self):
        return {'type': 3, 'origin': 0, 'destiny': Communicator.SERVID, 'sequence':0}
    
    def _treatMessage(self, bytesMessage):
        shouldStop = False

        messageType = struct.unpack("H", bytesMessage[0:2])[0]
        
        if  messageType == 4:

            sMsg = BaseHeader()
            message = {'type': 1, 'origin': self.myID, 'destiny': Communicator.SERVID, 'sequence':0}
            sMsg.setAttr(message)
            bMsg = sMsg.toBytes()

            print('{}: sending {!r}'.format(self.sock.getsockname(), bMsg), file=sys.stderr)
            self.sock.send(bMsg)

            shouldStop = True
        
        if messageType == 5:
            sMsg = Parameter2BMessage()
            sMsg.fromBytes(bytesMessage)
            print(f"< Message from {sMsg.header.origin}: {sMsg.message}")
            

        return shouldStop               
    
    def answerRequestsUntilMustClose(self):
        shouldStop = False
        while(not shouldStop):
            print("Esperando mensagem!")
            data = self.sock.recv(1024)

            shouldStop = self._treatMessage(data)
        
        self.disconnectFromServer()

    
def runExhibitor():

    exhibitor = Exhibitor()

    if(exhibitor.connectWith(sys.argv[1], int(sys.argv[2]))):
        print("Se conectou!")
        exhibitor.answerRequestsUntilMustClose()
    else:
        print("Program shutdown!")
        exit(1)
    
    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)
    
    runExhibitor()