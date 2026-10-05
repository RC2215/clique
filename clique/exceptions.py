from click import ClickException


class CliqueException(ClickException):
    pass


class LeaderException(CliqueException):
    pass
