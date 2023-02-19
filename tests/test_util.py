from kt.util import Logger


class TestUtil:
    def test_get_logger(self):
        target = Logger().get_logger()

        assert type(target).__name__ == "RootLogger"
