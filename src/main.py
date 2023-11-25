import PySimpleGUI as sg
import serial
import threading
import queue
from comms import Comms
import time


sg.theme("Default1")

device_label = sg.Text("Device")
device_textbox = sg.InputText(font="Courier 10", size=(35, 1))
connect_device_button = sg.Button("Connect")

settings_button = sg.Button("Settings")
debug_mode_toggle = sg.Checkbox("Debug Mode", default=True, key="debug_toggle", enable_events=True)

message_input_label = sg.Text("Message")
message_input_textbox = sg.InputText(font="Courier 10", key="message_input_textbox", size=(35, 1))
message_input_button = sg.Button("Send")

message_log_label = sg.Text("Message Log")
message_log_textbox = sg.Multiline(size=(50, 10), font="Courier 10")

debug_log_label = sg.Text("Debug Log")
debug_log_textbox = sg.Multiline(size=(50, 10), font="Courier 10")

message_log_textbox.Disabled = True
debug_log_textbox.Disabled = True
message_input_textbox.Disabled = True
message_input_button.Disabled = True

main_layout = [[device_label, device_textbox, connect_device_button],
          [settings_button, debug_mode_toggle],
          [message_input_label, message_input_textbox, message_input_button],
          [message_log_label],
          [message_log_textbox],
          [debug_log_label],
          [debug_log_textbox]]

#############################################################

debug_mode = True

freq = 869500000 # 868000000
power = 2
bandwidth = 125
spread = 12

input_queue = queue.Queue()
input_queue_lock = threading.Lock()

output_queue = queue.Queue()
output_queue_lock = threading.Lock()

debug_queue = queue.Queue()
debug_queue_lock = threading.Lock()

#############################################################

main_window = sg.Window("LoStik Lora Chat", main_layout, icon="lora.ico", finalize=True)
main_window["message_input_textbox"].bind("<Return>", "_Enter")

while True:
    event, values = main_window.read(timeout=100)
    # print(f"Event: {event}, Values: {values}")

    with debug_queue_lock:
        while not debug_queue.empty():
            debug_data = debug_queue.get()
            current_debug_lines = main_window[debug_log_textbox.key].get()
            if debug_mode:
                if current_debug_lines:
                    current_debug_lines = current_debug_lines + "\n"
                debug_log_textbox.update(current_debug_lines + debug_data)
                debug_log_textbox.set_vscroll_position(1.0)  # Scroll to bottom

    with output_queue_lock:
        while not output_queue.empty():
            message_data = output_queue.get()
            current_message_lines = main_window[message_log_textbox.key].get()
            if debug_mode:
                if current_message_lines:
                    current_message_lines = current_message_lines + "\n"
                message_log_textbox.update(current_message_lines + message_data)
                message_log_textbox.set_vscroll_position(1.0)  # Scroll to bottom

    if event == sg.WIN_CLOSED:
        with input_queue_lock:
            input_queue.put("$ABORT$")
        time.sleep(1)
        break
    elif event == "Settings":
        freq_input_label = sg.Text("Freq", size=(10, None))
        freq_input_textbox = sg.InputText(str(freq))

        power_input_label = sg.Text("Power", size=(10, None))
        power_input_textbox = sg.InputText(str(power))

        bandwidth_input_label = sg.Text("Bandwidth", size=(10, None))
        bandwidth_input_textbox = sg.InputText(str(bandwidth))

        spread_input_label = sg.Text("Spread", size=(10, None))
        spread_input_textbox = sg.InputText(str(spread))

        save_settings_button = sg.Button("Save")
        cancel_settings_button = sg.Button("Cancel")

        settings_layout = [[freq_input_label, freq_input_textbox],
                           [power_input_label, power_input_textbox],
                           [bandwidth_input_label, bandwidth_input_textbox],
                           [spread_input_label, spread_input_textbox],
                           [save_settings_button, cancel_settings_button]]

        settings_window = sg.Window("Settings", settings_layout, icon="lora.ico")

        while True:
            settings_event, settings_values = settings_window.read(timeout=100)
            # print(f"Settings Event: {settings_event}, Values: {settings_values}")
            if settings_event == sg.WIN_CLOSED:
                break
            elif settings_event == "Save":
                temp_freq = settings_values[freq_input_textbox.key]
                try:
                    temp_freq = int(temp_freq)
                except ValueError:
                    sg.popup("Frequency must be an integer", title="Error", icon="lora.ico")
                    continue

                temp_power = settings_values[power_input_textbox.key]
                try:
                    temp_power = int(temp_power)
                    if not (2 <= temp_power <= 17):
                        sg.popup("Power must be between 2 and 17", title="Error", icon="lora.ico")
                        continue
                except ValueError:
                    sg.popup("Power must be an integer", title="Error", icon="lora.ico")
                    continue

                temp_bandwidth = settings_values[bandwidth_input_textbox.key]
                try:
                    temp_bandwidth = int(temp_bandwidth)
                    if not (temp_bandwidth in [125, 250, 500]):
                        sg.popup("Bandwidth must be 125, 250 or 500", title="Error", icon="lora.ico")
                        continue
                except ValueError:
                    sg.popup("Bandwidth must be an integer", title="Error", icon="lora.ico")
                    continue

                temp_spread = settings_values[spread_input_textbox.key]
                try:
                    temp_spread = int(temp_spread)
                    if not (7 <= temp_spread <= 12):
                        sg.popup("Spread must be between 7 and 12", title="Error", icon="lora.ico")
                        continue
                except ValueError:
                    sg.popup("Spread must be an integer", title="Error", icon="lora.ico")
                    continue

                freq = temp_freq
                power = temp_power
                bandwidth = temp_bandwidth
                spread = temp_spread
                break
            elif settings_event == "Cancel":
                break

        settings_window.close()

    elif event == "Connect":
        try:
            serial_port = serial.Serial(values[device_textbox.key], 57600)
            if not serial_port.isOpen():
                serial_port.open()
            serial_port.bytesize = 8
            serial_port.parity = "N"
            serial_port.stopbits = 1
            serial_port.timeout = 5

            settings = (freq, power, bandwidth, spread)
            queues = (input_queue, input_queue_lock, output_queue, output_queue_lock, debug_queue, debug_queue_lock)
            comms_handler = Comms(serial_port, settings, queues)
            comms_handler.daemon = True
            comms_handler.start()

            device_textbox.update(disabled=True)
            connect_device_button.update(disabled=True)
            settings_button.update(disabled=True)

            message_input_textbox.update(disabled=False)
            message_input_button.update(disabled=False)
        except Exception as e:
            sg.popup(f"Communication error:\n\n{e}", title="Error", icon="lora.ico")
    elif (event == "Send") or (event == "message_input_textbox" + "_Enter"):
        new_message = values[message_input_textbox.key]
        with input_queue_lock:
            input_queue.put(new_message)
        message_input_textbox.update("")

    elif values["debug_toggle"]:
        debug_mode = True
    elif not values["debug_toggle"]:
        debug_mode = False

main_window.close()