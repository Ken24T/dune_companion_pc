"""
Network utility functions for the Dune Companion PC App.
"""
import socket
from app.utils.logger import get_logger

logger = get_logger(__name__)

def check_internet_connection(host="8.8.8.8", port=53, timeout=3) -> bool:
    """
    Check for internet connectivity by attempting to connect to a known host.

    Args:
        host (str): The host to connect to (default is Google's DNS server).
        port (int): The port to connect to (default is 53, DNS).
        timeout (int): Connection timeout in seconds.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.debug(f"Internet connection check: Successful connection to {host}:{port}")
        return True
    except socket.error as ex:
        logger.warning(f"Internet connection check: Failed to connect to {host}:{port} - {ex}")
        return False

if __name__ == '__main__':
    # For basic testing
    if check_internet_connection():
        print("Internet connection is available.")
    else:
        print("No internet connection.")
