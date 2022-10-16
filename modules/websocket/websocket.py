import json
import multiprocessing
import random
from abc import ABC

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket


class TornadoWSServer(tornado.websocket.WebSocketHandler, ABC):
    clients = set()

    def open(self):
        TornadoWSServer.clients.add(self)
        print(self.request)

    def on_close(self):
        TornadoWSServer.clients.remove(self)

    def on_message(self, message):
        print(f"R<<< {message}")

    def check_origin(self, origin):
        return True

    @classmethod
    def send_message(cls, message: str):
        if message != "null":
            for client in cls.clients:
                # print(f"S>>> {message}")
                client.write_message(message)



def random_number():
    return int(random.uniform(0, 1000))


class WebSocketHandler(multiprocessing.Process):
    def __init__(self, ws_commands: multiprocessing.Queue, telemetry_json_output: multiprocessing.Queue):
        super().__init__()
        self.telemetry_json_output = telemetry_json_output
        self.ws_commands = ws_commands
        self.startWSS()

    def startWSS(self):

        wss = tornado.web.Application(
            [(r"/websocket", TornadoWSServer)],
            websocket_ping_interval=10,
            websocket_ping_timeout=30,
        )

        wss.listen(33845)

        io_loop = tornado.ioloop.IOLoop.current()

        periodic_callback = tornado.ioloop.PeriodicCallback(
            lambda: TornadoWSServer.send_message(str(self.sample())), 50
        )

        periodic_callback.start()

        io_loop.start()

    def sample(self):

        json_data = None
        #print(f"LEN OF TELE? {self.telemetry_json_output.qsize()}")
        while not self.telemetry_json_output.empty():
            json_data = self.telemetry_json_output.get()
            # print(f"WSHandler READING TELEMETRY OUTPUT QUEUE: {json_data}")
        return json.dumps(json_data)