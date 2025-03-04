# -*- coding: utf-8 -*-
#
# Copyright 2023 NXP
#
# SPDX-License-Identifier: MIT


from unittest.mock import MagicMock, call

import pytest

from fc_client.client import Client


class TestClient:
    @pytest.mark.parametrize("mode", ["normal", "detail"])
    def test_status(self, mocker, capsys, mode):
        class Args:
            resource = "imx8mm-evk-sh11"
            farm_type = "bsp"
            device_type = "imx8mm-evk"

        class Output:
            def __init__(self):
                self.text = None

            def __call__(self, mode):
                if mode == "normal":
                    self.text = '[["imx8mm-evk-sh11", "bsp", "idle", ""]]'
                else:
                    self.text = '[["imx8mm-evk-sh11", "bsp", "idle", "", "[{}]"]]'
                return self

        mocker.patch(
            "requests.get",
            return_value=Output()(mode),
        )

        Client.status(Args)

        output = capsys.readouterr()[0]
        assert output in (
            """+-----------------+------+--------+---------+------+
|     Resource    | Farm | Status | Comment | Info |
+-----------------+------+--------+---------+------+
| imx8mm-evk-sh11 | bsp  |  idle  |         | [{}] |
+-----------------+------+--------+---------+------+
""",
            """+-----------------+------+--------+---------+
|     Resource    | Farm | Status | Comment |
+-----------------+------+--------+---------+
| imx8mm-evk-sh11 | bsp  |  idle  |         |
+-----------------+------+--------+---------+
""",
        )

    def test_lock(self, mocker):
        class Args:
            resource = "imx8mm-evk-sh11"

        reserve_cmd = mocker.patch("subprocess.Popen", return_value=MagicMock())
        lock_cmd = mocker.patch("subprocess.call", return_value=MagicMock())
        Client.lock(Args)

        reserve_cmd.assert_called_with(
            ["labgrid-client", "reserve", "--wait", "name=imx8mm-evk-sh11"],
            stderr=-1,
            stdout=-1,
        )
        lock_cmd.assert_called_with(["labgrid-client", "-p", "imx8mm-evk-sh11", "lock"])

    def test_unlock(self, mocker):
        class Args:
            resource = "imx8mm-evk-sh11"

        mocker.patch("os.environ.get", return_value="test")
        mocker.patch(
            "subprocess.getstatusoutput",
            return_value=(
                0,
                """Place 'imx8mm-evk-sh11':
  matches:
    */imx8mm-evk-sh11/*
  acquired: test/test
  acquired resources:
  created: 2022-03-03 10:38:04.453874
  changed: 2023-03-28 16:17:05.881561
  reservation: AU7AKIDBHT
""",
            ),
        )
        mocker.patch(
            "subprocess.check_output",
            return_value="""Reservation 'AU7AKIDBHT':
  owner: test/test
  token: AU7AKIDBHT
  state: acquired
  filters:
    main: name=imx8mm-evk-sh11
  allocations:
    main: imx8mm-evk-sh11
  created: 2023-03-28 16:40:36.097286
  timeout: 2023-03-28 16:46:18.902555
""",
        )
        calls = [
            call(["labgrid-client", "cancel-reservation", "AU7AKIDBHT"]),
            call(["labgrid-client", "-p", "imx8mm-evk-sh11", "unlock"]),
        ]
        labgird_free = mocker.patch("subprocess.call", return_value=MagicMock())

        Client.unlock(Args)

        labgird_free.assert_has_calls(calls)
