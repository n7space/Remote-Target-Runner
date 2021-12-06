import os
from libs.UartIoHandler import UartIoHandler

sshAddress = os.environ['TASTE_RASPI_ADDRESS']
sshPort = os.environ['TASTE_RASPI_PORT']
sshPassword = os.environ['TASTE_RASPI_PASSWORD']
sshUser = os.environ['TASTE_RASPI_USER']

uartIoHandlerID = 4
uartIoHandlerAddress = sshAddress
uartIoHandlerUserName = sshUser
uartIoHandlerPassword = sshPassword
uartIoHandlerBaudrate = 115200
uartIoHandlerPort = 5005
uartIoHandlerPath = "/dev/ttyACM0"
uartIoHandlerVerbose = True

uartIoHandler = {   "uartId" : uartIoHandlerID,
                    "address" : uartIoHandlerAddress,
                    "username" : uartIoHandlerUserName,
                    "password" : uartIoHandlerPassword,
                    "baudrate" : uartIoHandlerBaudrate,
                    "port" : uartIoHandlerPort,
                    "path" : uartIoHandlerPath,
                    "verbose" : uartIoHandlerVerbose}

handler = UartIoHandler(
                uartIoHandler["address"],
                uartIoHandler["username"],
                uartIoHandler["password"],
                uartIoHandler["path"],
                uartIoHandler["baudrate"],
                uartIoHandler["port"],
                debug = True,
            )
handler.open()


