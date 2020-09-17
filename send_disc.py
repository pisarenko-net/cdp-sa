import threading
import time

import zmq

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.set_hwm(10)
socket.connect("tcp://127.0.0.1:7943")

def create_target(socket):
    def _generate_messages():
        while True:
            print('Sending message')
            socket.send_multipart([b'disc', b'found'])
            #self.state_sender.send('playback', 'something is happening here')
            time.sleep(5)
    return _generate_messages

send_thread = threading.Thread(
    target=create_target(socket),
    name='cli test'
)
send_thread.start()

