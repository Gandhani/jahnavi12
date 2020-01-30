import traceback

from _pytest.logging import LogCaptureFixture
from click.testing import Result


def assert_no_logging_messages_or_tracebacks(my_caplog, click_result):
    """
    Use this assertion in all CLI tests unless you have a very good reason.

    Without this assertion, it is easy to let errors and tracebacks bubble up
    to users without being detected, unless you are manually inspecting the
    console output (stderr and stdout), as well as logging output from every
    test.

    Usage:

    ```
    def test_my_stuff(caplog):
        ...
        result = runner.invoke(...)
        ...
        assert_no_logging_messages_or_tracebacks(caplog, result)
    ```

    :param my_caplog: the caplog pytest fixutre
    :param click_result: the Result object returned from click runner.invoke()
    """
    assert isinstance(
        my_caplog, LogCaptureFixture
    ), "Please pass in the caplog object from your test."
    assert isinstance(
        click_result, Result
    ), "Please pass in the click runner invoke result object from your test."

    messages = my_caplog.messages
    assert isinstance(messages, list)
    if messages:
        print(messages)
    assert not messages

    if click_result.exc_info:
        # introspect the call stack to make sure no exceptions found there way through
        # https://docs.python.org/2/library/sys.html#sys.exc_info
        _type, value, _traceback = click_result.exc_info
        if not isinstance(value, SystemExit):
            # SystemExit is a known "good" exit type
            print("".join(traceback.format_tb(_traceback)))
            assert False, "Found exception of type {} with message {}".format(
                _type, value
            )
    assert not click_result.exception, "Found exception {}".format(
        click_result.exception
    )

    assert (
        "traceback" not in click_result.output.lower()
    ), "Found a traceback in the console output: {}".format(click_result.output)
    assert (
        "traceback" not in click_result.stdout.lower()
    ), "Found a traceback in the console output: {}".format(click_result.stdout)
