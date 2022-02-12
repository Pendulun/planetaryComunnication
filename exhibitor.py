from lib2to3.pytree import Base
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

            shouldStop = self._treatKillMsg()
        
        elif messageType == 5:

            self._treatMSGMessage(bytesMessage)
        
        elif messageType == 7:

            self._treatCLISTMessage(bytesMessage)
        
        elif messageType == 9:

            self._treatPLANETMessage(bytesMessage)
        
        elif messageType == 10:

            self._treatPLANETLISTMessage(bytesMessage)
            
        return shouldStop            

    def _treatKillMsg(self):
        print("< kill")
        self._sendOKToServer()

        shouldStop = True

        return shouldStop
    
    def _treatMSGMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"< Message from {sMsg.header.origin}: {sMsg.message}")
    
    def _treatCLISTMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"< CLIST: {sMsg.message}")

        self._sendOKToServer()
    
    def _treatPLANETMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"< PLANET of {sMsg.header.destiny}: {sMsg.message}")
    
    def _treatPLANETLISTMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"< PLANETLIST: {sMsg.message}")

    def _sendOKToServer(self):
        sMsg = BaseHeader()
        message = {'type': 1, 'origin': self.myID, 'destiny': Communicator.SERVID, 'sequence':0}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        print('{}: sending {}'.format(self.sock.getsockname(), sMsg), file=sys.stderr)
        self.sock.send(bMsg)
    
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