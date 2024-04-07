import socket

ip = '127.0.0.1'
port = 5001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((ip, port))

sock.listen(1)
print('Listening...')

conn, addr = sock.accept()
print('Connected.')

#msg = b'Hello!'
msg = f'Hello'.encode("utf-8")

conn.send(msg)
print(f'Sent message [{msg}].')

response_msg = conn.recv(128).decode("utf-8")
print(f'Received message [{response_msg}]')
conn.close()
