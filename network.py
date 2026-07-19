import socket


def get_lan_ip():
    try:
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        connection.connect(("8.8.8.8", 80))
        ip = connection.getsockname()[0]
        connection.close()
        return ip
    except OSError:
        return "127.0.0.1"
