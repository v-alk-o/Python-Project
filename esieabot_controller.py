from discord import Client, Intents, Message
from gpiozero import Robot
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from mjpeg_server import *
import functools
import asyncio
import json
import sys
from custom_logger import CustomLogger



class EsieabotController(Client):
    def __init__(self):
        super().__init__(intents=Intents.all())
        self.initialized = False

    
    def load_config(self, filename="settings.json"):
        try:
            with open(filename, 'r') as settings_file:
                settings = json.load(settings_file)

            self.token = settings["token"]
            if not isinstance(self.token, str):
                sys.exit("Expected ['token'] parameter to be a String")

            logging_level = settings["logging_level"]
            if not isinstance(logging_level, str) or logging_level not in logging._levelToName.values():
                sys.exit(f"Expected ['logging_level'] parameter to be one of the following : {logging._levelToName.values()}")

            self.streaming_server_port = settings["streaming_server_port"]
            if not isinstance(self.streaming_server_port, int) or not (1024 <= self.streaming_server_port <= 65535):
                sys.exit(f"Expected ['streaming_server_port'] parameter to be a port number between 1024 and 65535") 

            robot_dict = settings["robot"]
            if not isinstance(robot_dict, dict):
                sys.exit(f"Expected ['robot'] parameter to be a dictionnary")

            robot_dict_expected_keys = ["left_motor_forward_pin", "left_motor_backward_pin", "right_motor_forward_pin", "right_motor_backward_pin"]
            for expected_key in robot_dict_expected_keys: 
                if expected_key not in robot_dict.keys() or not isinstance(robot_dict[expected_key], int) or not (0 <= robot_dict[expected_key] <= 40):
                    sys.exit(f"Expected ['robot']['{expected_key}'] parameter to be a GPIO port number between 0 and 40")
                robot_lmfp = settings["robot"]["left_motor_forward_pin"]
                robot_lmbp = settings["robot"]["left_motor_backward_pin"]
                robot_rmfp = settings["robot"]["right_motor_forward_pin"]
                robot_rmbp = settings["robot"]["right_motor_backward_pin"]

        except OSError as e:
            sys.exit(f"Could not open file '{filename}'")
        except json.decoder.JSONDecodeError:
            sys.exit(f"Malformed JSON configuration file '{filename}'")
        except KeyError as e:
            sys.exit(f"Configuration file has no key {e}")

        self.logger = CustomLogger.get_logger(logging_level)
        self.robot = Robot((robot_lmfp, robot_lmbp), (robot_rmfp, robot_rmbp))
        Picamera2.set_logging(logging_level, msg=self.logger.handlers[0].formatter._fmt)
        self.picam2 = Picamera2()
        self.initialized = True

    
    def run(self):
        if self.initialized:
            super().run(self.token, log_handler=None)
        else:
            sys.exit("Could not run an unitialized ESIEAbot Controller. Initialize it from file with 'load_config' method")


    def start_webserver(self):
        self.server = StreamingServer(('', self.streaming_server_port), StreamingHandler)
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (640, 480)}))
        self.picam2.start_recording(JpegEncoder(), FileOutput(output))
        try:
            self.server.serve_forever()
        except OSError:
            self.logger.error("Could not start streaming server (Provided port might be alreay used)")
        finally:
            self.picam2.stop_recording()


    async def async_start_webserver(self):
        func = functools.partial(self.start_webserver)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)


    async def on_ready(self):
        self.logger.info("The bot is ready !")


    async def on_message(self, message):
        message.content = message.content.upper()
        if message.content == "START STREAMING":
            await message.channel.send("Starting streaming...")
            task = asyncio.create_task(self.async_start_webserver())
            self.logger.info("Starting streaming...")

        elif message.content == "STOP STREAMING":
            self.logger.info("Finisihed streaming !")
            self.picam2.stop_recording()
            self.server.socket.close()
            await message.channel.send("Finished streaming !")

        elif message.content == "H":
            await message.channel.send("Turning left !")
            self.robot.left(0.5)
            self.logger.info("Turning left !")

        elif message.content == "K":
            await message.channel.send("Going forward !")
            self.robot.forward(0.5)
            self.logger.info("Going forward !")

        elif message.content == "J":
            await message.channel.send("Going backward !")
            self.robot.backward(0.5)
            self.logger.info("Going backward !")

        elif message.content == "L":
            await message.channel.send("Turning right !")
            self.robot.right(0.5)
            self.logger.info("Turning right !")

        elif message.content == "S":
            await message.channel.send("Stopping !")
            self.robot.stop()
            self.logger.info("Stopping !")

        elif message.content == "END":
            await message.channel.send("Ending the bot !")
            self.logger.info("End program")
            await self.close()
        else:
            pass



if __name__ == '__main__':
    bot = EsieabotController()
    bot.load_config("settings.json")
    bot.run()
