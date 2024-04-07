import socket

ip = '127.0.0.1'
port = 5001

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

conn.connect((ip, port))
print('Connected.')

msg = conn.recv(128).decode("utf-8")
print(f'Received message [{msg}]')

response_msg = f'Hello! Your message was [{msg}]'.encode("utf-8")

conn.send(response_msg)
print(f'Sent message [{response_msg}].')
conn.close()
