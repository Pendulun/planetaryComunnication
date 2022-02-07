import socket
import sys
from common import SimpleMessage
from common import BaseHeader

def usage():
    print("python emitter.py <serverIP> <port>")

def runExhibitor():
    server_address = (sys.argv[1], int(sys.argv[2]))

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    print('connecting to {} port {}'.format(*server_address), file=sys.stderr)

    sock.connect(server_address)

    #Enviar mensagem HI
    sMsg = BaseHeader()
    message = {'type': 3, 'origin': 0, 'destiny': 0, 'sequence':0}
    sMsg.setAttr(message)
    bMsg = sMsg.toBytes()

    print('{}: sending {!r}'.format(sock.getsockname(), bMsg), file=sys.stderr)
    sock.send(bMsg)

    #Receber resposta
    data = sock.recv(1024)
    sMsg.fromBytes(data)
    print('{}: received {}'.format(sock.getsockname(), data), file=sys.stderr)

    if not data:
        print('closing socket', sock.getsockname(), file=sys.stderr)
        sock.close()
    else:
        print(f"My ID is: {sMsg.destiny}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)
    
    runExhibitor()