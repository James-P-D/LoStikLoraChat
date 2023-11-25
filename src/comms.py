import threading
import serial
import queue
import time


class Comms(threading.Thread):

    def __init__(self, serial_port, settings, queues):
        super(Comms, self).__init__()
        self.serial_port = serial_port
        (self.freq, self.power, self.bandwidth, self.spread) = settings
        (self.input_queue, self.input_queue_lock,
         self.output_queue, self.output_queue_lock,
         self.debug_queue, self.debug_queue_lock) = queues

        self.send_cmd(bytearray(f"radio cw off", encoding="utf8"))
        self.send_cmd(bytearray(f"radio set pwr {self.power}", encoding="utf8"))
        self.send_cmd(bytearray(f"radio set bw {self.bandwidth}", encoding="utf8"))
        self.send_cmd(bytearray(f"radio set freq {self.freq}", encoding="utf8"))
        self.send_cmd(bytearray(f"radio set sf sf{self.spread}", encoding="utf8"))
        self.send_cmd(bytearray(f"radio set wdt 0", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get bt", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get mod", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get freq", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get pwr", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get sf", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get afcbw", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get bitrate", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get fdev", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get prlen", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get crc", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get iqi", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get cr", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get wdt", encoding="utf8"))
        self.send_cmd(bytearray(f"radio get bw", encoding="utf8"))
        self.send_cmd(bytearray(f"mac pause", encoding="utf8"))

    def send_cmd(self, command):
        with self.debug_queue_lock:
            self.debug_queue.put("> " + command.decode("utf8"))
            print("> " + command.decode("utf8"))

        self.serial_port.write(command + b"\r\n")
        response = self.serial_port.readline()
        with self.debug_queue_lock:
            self.debug_queue.put(response.decode("utf8").rstrip())
            print(response.decode("utf8").rstrip())
        return response

    def run(self):
        while True:
            # time.sleep(0.1)
            send_data = ""
            with self.input_queue_lock:
                if not self.input_queue.empty():
                    send_data = bytes(self.input_queue.get() + "\r\n", encoding="UTF-8")

                    if send_data == "$ABORT$":
                        self.serial_port.close()
                        return  # should this be break?
                    else:
                        send_data_encoded = "".join("{:02x}".format(x) for x in send_data)
                        self.send_cmd(bytearray(f"radio rxstop", encoding="utf8"))
                        # TODO: Check for busy here?
                        self.send_cmd(bytearray(f"radio tx {send_data_encoded}", encoding="utf8"))
                        # time.sleep(0.5 + 0.01 * int(len(send_data_encoded)*2))

            if send_data:
                with self.output_queue_lock:
                    self.output_queue.put("SEND: " + send_data.decode("utf8").rstrip())

            recv_data = self.send_cmd(bytearray(f"radio rx 0", encoding="utf8")).decode("utf-8")
            if recv_data.startswith("radio_rx"):
                trimmed = recv_data[10:]
                readable = bytes.fromhex(trimmed).decode()
                # TODO: Check for busy here
                if readable:
                    with self.output_queue_lock:
                        self.output_queue.put("RECV: " + readable.rstrip())
