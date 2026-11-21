import re
import sys

import pytest

from Magics.__main__ import main, selfcheck


def test_selfcheck(capsys):
    selfcheck()

    stdout, stderr = capsys.readouterr()

    assert "Found:" in stdout
    assert "Library:" in stdout
    assert "Magics home:" in stdout
    assert "Your system is ready." in stdout

    assert "You are using an old version of magics" not in stdout


def test_main_success(capsys):
    sys.argv = ["program", "selfcheck"]
    main()
    stdout, stderr = capsys.readouterr()
    assert "Your system is ready." in stdout


def test_main_failure_no_command(capsys):
    sys.argv = ["program"]
    with pytest.raises(SystemExit) as ex:
        main()
    ex.match("2")
    stdout, stderr = capsys.readouterr()
    assert "program: error: the following arguments are required: command" in stderr


def test_main_failure_unknown_command(capsys):
    sys.argv = ["program", "foobar"]
    with pytest.raises(RuntimeError) as ex:
        main()
    ex.match(re.escape("Command not recognised 'foobar'. See usage with --help."))
