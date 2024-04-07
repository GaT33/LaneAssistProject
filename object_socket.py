import socket
import select
import pickle
import datetime

from typing import *


class ObjectSocketParams:
    OBJECT_HEADER_SIZE_BYTES = 4 #primii 4 bytes ai fiecarui mesaj trimis contin informatii despre dimensiunea totala a obiectului
    DEFAULT_TIMEOUT_S = 1 #valoare timeout
    CHUNK_SIZE_BYTES = 1024 #dimensiune trimisa pe bucata prin socket


class ObjectSenderSocket:
    ip: str
    port: int
    sock: socket.socket
    conn: socket.socket
    print_when_awaiting_receiver: bool
    print_when_sending_object: bool
    
    #definire variable
    
    #se creeaza constructor
    def __init__(self, ip: str, port: int,
                 print_when_awaiting_receiver: bool = False,
                 print_when_sending_object: bool = False):
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port)) #atriubuie socket ip,port
        self.conn = None #stocare conexiune

        self.print_when_awaiting_receiver = print_when_awaiting_receiver
        self.print_when_sending_object = print_when_sending_object

        self.await_receiver_conection()

    def await_receiver_conection(self):

        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] awaiting receiver connection...')
            
            #print data, ora,ip-ul,portul

        self.sock.listen(1) #asteapta conexiunea 
        self.conn, _ = self.sock.accept()  #stocheaza conexiuna in conn, _ este folosit ptr a stoca si a nu folosi,ip,port

        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] receiver connected')

    def close(self):
        self.conn.close()
        self.conn = None
        
    #referinta la obiectul curent, functia returneaza un bool
    def is_connected(self) -> bool:
        return self.conn is not None #verifica daca self.conn este diferita de None si returneaza true in cazul acesta
    #functia care primeste referinta la obiect si un obiect, oricare
    def send_object(self, obj: Any):
        data = pickle.dumps(obj) #transformare in bytes
        data_size = len(data)
        data_size_encoded = data_size.to_bytes(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES, 'little') #transforma dimensiunea datelor in binar, folosind dimensiunea declarata mai sus, little e LSB
        self.conn.sendall(data_size_encoded) #trimite antetul, asigura transmiterea tuturor datelor (se blocheaza)
        self.conn.sendall(data) #trimite data
        if self.print_when_sending_object:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] Sent object of size {data_size} bytes.')



class ObjectReceiverSocket:
    ip: str
    port: int
    conn: socket.socket
    print_when_connecting_to_sender: bool
    print_when_receiving_object: bool

    def __init__(self, ip: str, port: int,
                 print_when_connecting_to_sender: bool = False,
                 print_when_receiving_object: bool = False):
        self.ip = ip
        self.port = port
        self.print_when_connecting_to_sender = print_when_connecting_to_sender
        self.print_when_receiving_object = print_when_receiving_object

        self.connect_to_sender()

    def connect_to_sender(self):

        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connecting to sender...')

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.ip, self.port))

        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connected to sender')

    def close(self):
        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        return self.conn is not None

    def recv_object(self) -> Any:
        obj_size_bytes = self._recv_object_size() #primeste dimensiunea obiectului
        data = self._recv_all(obj_size_bytes)  #primeste bytes
        obj = pickle.loads(data) #obtinere obiect original
        if self.print_when_receiving_object:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] Received object of size {obj_size_bytes} bytes.')
        return obj

    def _recv_with_timeout(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> Optional[bytes]: #ori byte ori None
        rlist, _1, _2 = select.select([self.conn], [], [], timeout_s)
        #rlist contine socket-urile care au variabilele
        if rlist:
            data = self.conn.recv(n_bytes) #primeste datele, citeste un numar de biti
            return data
        else:
            return None  # Only returned on timeout

    def _recv_all(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> bytes:
        data = []
        left_to_recv = n_bytes
        while left_to_recv > 0:
            desired_chunk_size = min(ObjectSocketParams.CHUNK_SIZE_BYTES, left_to_recv) 
            chunk = self._recv_with_timeout(desired_chunk_size, timeout_s)
            if chunk is not None:
                data += [chunk] 
                left_to_recv -= len(chunk)
            else:  # no more data incoming, timeout
                bytes_received = sum(map(len, data)) #calculare suma bytes, adunand lungimea fiecarei bucati
                raise socket.error(f'Timeout elapsed without any new data being received. '
                                   f'{bytes_received} / {n_bytes} bytes received.')
        data = b''.join(data) #concatenare
        return data
    #returneaza dimensiunea obiectului care urmeaza sa fie trimis
    def _recv_object_size(self) -> int:
        data = self._recv_all(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES)
        obj_size_bytes = int.from_bytes(data, 'little')
        return obj_size_bytes
        
        


