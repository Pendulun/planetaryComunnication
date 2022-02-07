import select
import socket
import sys
import queue
import struct
import random
from common import SimpleMessage
from common import BaseHeader

def usage():
    print("Usage: python server.py <port>")

class Server:
    MINEXIID = 2**12
    MAXEXID = (2**13)-1
    MINEMID = 1
    MAXEMID = (2**12) - 1
    SERVID = (2**16) - 1

    def __init__(self):
        self.sock = -1
        self.sequence = 0
        self.exihibitors = []
        self.emitters = []
        self.clientsInfo = {}
    
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

    def run(self):

        if not self.sock:
            return

        # Listen for incoming connections
        self.sock.listen(5)

        # Sockets from which we expect to read
        inputs = [self.sock]

        # Sockets to which we expect to write
        outputs = []

        # Outgoing message queues (socket:Queue)
        message_queues = {}

        client_ids = {}

        while inputs:

            # Wait for at least one of the sockets to be
            # ready for processing
            print('waiting for the next event', file=sys.stderr)
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            
            # Handle inputs
            for s in readable:

                if s is self.sock:
                    # A "readable" socket is ready to accept a connection
                    connection, client_address = s.accept()
                    print('  connection from', client_address, file=sys.stderr)
                    connection.setblocking(0)
                    inputs.append(connection)

                    # Give the connection a queue for data
                    # we want to send
                    message_queues[connection] = queue.Queue()
                else:
                    data = s.recv(1024)
                    if data:
                        print('  received {} from {}'.format(data, s.getpeername()), file=sys.stderr,)
                    
                        sockToAnswer, responseMessage = self.treatMessage(data, s)

                        if sockToAnswer:
                            message_queues[sockToAnswer].put(responseMessage)
                            if sockToAnswer not in outputs:
                                outputs.append(sockToAnswer)
                        
                    else:
                        # Interpret empty result as closed connection
                        print('  closing', client_address, file=sys.stderr)
                        # Stop listening for input on the connection
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()

                        # Remove message queue
                        del message_queues[s]

            # Handle outputs
            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    # No messages waiting so stop checking
                    # for writability.
                    print('  ', s.getpeername(), 'queue empty', file=sys.stderr)
                    outputs.remove(s)
                else:
                    print('  sending {} to {}'.format(next_msg, s.getpeername()), file=sys.stderr)
                    s.send(next_msg)

            # Handle "exceptional conditions"
            for s in exceptional:
                print('exception condition on', s.getpeername(), file=sys.stderr)
                # Stop listening for input on the connection
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s] 

    def treatMessage(self, bytesMessage, inSocket):
        responseMessage = None
        sockToAnswer = -1

        messageType = struct.unpack("H", bytesMessage[0:2])[0]
        
        if  messageType == 3:
            self.sequence += 1
            inMessage = BaseHeader()
            inMessage.fromBytes(bytesMessage)
            
            if inMessage.origin >= 2**12 and inMessage.origin < 2**13:
                #É um emissor
                pass
            elif inMessage.origin == 0:
                #É um exibidor
                myMessage = BaseHeader()
                newId = self.generateExihibitorId()
                print(f"GENERATED ID: {newId}")
                
                message = {}
                message['origin'] = Server.SERVID 
                message['destiny'] = newId
                message['type'] = 1
                message['sequence'] = self.sequence
                myMessage.setAttr(message)
                responseMessage = myMessage.toBytes()

                self.clientsInfo[newId] = {'socket': inSocket}

                sockToAnswer = inSocket  

        return sockToAnswer, responseMessage                                   


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        exit(1)
    
    server = Server()
    server.createServerSocket(int(sys.argv[1]))
    server.run()
