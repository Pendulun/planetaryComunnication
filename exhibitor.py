import socket
import sys
from common import BaseHeader
from common import Client
from common import Communicator
from common import Parameter2BMessage

def usage():
    print("python emitter.py <serverIP>:<port>")

class Exhibitor(Client):

    def __init__(self):
        super().__init__()
    
    def _messageForHI(self):
        return {'type': Communicator.HI_MSG_ID, 'origin': Communicator.EXHIBITOR_HI_MSG_ID,
                'destiny': Communicator.SERVID, 'sequence':self.sequence}
    
    def answerRequestsUntilMustClose(self):
        shouldStop = False
        while(not shouldStop):
            data = self.sock.recv(1024)
            self.sequence += 1

            shouldStop = self._treatMessage(data)
        
        self.disconnectFromServer()
    
    def _treatMessage(self, bytesMessage):
        shouldStop = False

        sMsg = BaseHeader()
        sMsg.fromBytes(bytesMessage)

        messageType = sMsg.type
        
        if  messageType == Communicator.KILL_MSG_ID:

            shouldStop = self._treatKillMsg()
        
        elif messageType == Communicator.MSG_MSG_ID:

            self._treatMSGMessage(bytesMessage)
        
        elif messageType == Communicator.CLIST_MSG_ID:

            self._treatCLISTMessage(bytesMessage)
        
        elif messageType == Communicator.PLANET_MSG_ID:

            self._treatPLANETMessage(bytesMessage)
        
        elif messageType == Communicator.PLANETLIST_MSG_ID:

            self._treatPLANETLISTMessage(bytesMessage)
            
        return shouldStop            

    def _treatKillMsg(self):
        print("KILL< ")
        self._sendOKToServer()

        shouldStop = True

        return shouldStop
    
    def _treatMSGMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"MESSAGE from {sMsg.header.origin}< '{sMsg.message}'")
    
    def _treatCLISTMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"CLIST< '{sMsg.message}'")

        self._sendOKToServer()
    
    def _treatPLANETMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"PLANET of {sMsg.header.destiny}< '{sMsg.message}'")
    
    def _treatPLANETLISTMessage(self, bytesMessage):
        sMsg = Parameter2BMessage()
        sMsg.fromBytes(bytesMessage)
        print(f"PLANETLIST< '{sMsg.message}'")

    def _sendOKToServer(self):
        sMsg = BaseHeader()
        message = {'type': Communicator.OK_MSG_ID, 'origin': self.myID, 'destiny': Communicator.SERVID, 
                    'sequence':self.sequence}
        sMsg.setAttr(message)
        bMsg = sMsg.toBytes()

        self.sock.send(bMsg)


def runExhibitor():

    exhibitor = Exhibitor()

    serverAddr = sys.argv[1].split(":")

    if(len(serverAddr) == 2 and exhibitor.connectWith(serverAddr[0], int(serverAddr[1]))):
        exhibitor.answerRequestsUntilMustClose()
    else:
        print("Program shutdown!")
        exit(1)
    
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        exit(1)
    
    runExhibitor()