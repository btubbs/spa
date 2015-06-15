# We do most imports late here, inside functions, to make sure gevent
# monkeypatching works in the subprocess.

def run_echo_server(port):
    from gevent.monkey import patch_all
    patch_all()
    import spa
    class Echo(spa.Handler):
        def websocket(self):
            while True:
                msg = self.ws.receive()
                self.ws.send(msg)
    routes = (
        ('/', 'echo', Echo),
    )

    app = spa.App(routes)
    spa.run(app, port=port)


def test_echo():
    import multiprocessing
    import socket
    import time

    # get a random port
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    # start a server on that port
    p = multiprocessing.Process(target=run_echo_server, args=(port,))
    try:
        p.start()

        # wait for the port to be open.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tries = 0
        max_tries = 10
        while sock.connect_ex(('127.0.0.1', port)) != 0:
            time.sleep(0.1)
            tries += 1
            assert tries < max_tries, "Timed out waiting for websocket server"

        from websocket import create_connection
        ws = create_connection('ws://localhost:%s/' % port)
        ws.send('hey!')
        assert ws.recv() == 'hey!'
        ws.close()
    finally:
        p.terminate()
