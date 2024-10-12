import contextlib

from moto.server import ThreadedMotoServer

from configuration import MOCKED_MOTO_SERVER_PORT


@contextlib.contextmanager
def mock_boto():
    server = ThreadedMotoServer(port=MOCKED_MOTO_SERVER_PORT)
    server.start()
    yield
    server.stop()


if __name__ == "__main__":
    with mock_boto():
        while True:
            pass
