#!/usr/bin/env python

import os
import subprocess
from datetime import datetime
from sonic_py_common.general import getstatusoutput_noshell_pipe

GPIO_DIR = "/sys/class/gpio/"
GPIO_EXPORT_PATH = GPIO_DIR + "export"
POWER_LOSS_GPIO = "18" #TP_MB_PCA9555_PIN6
POWER_LOSS_GPIO_VALUE = GPIO_DIR + "gpio" + POWER_LOSS_GPIO + "/value"
POWER_LOSS_GPIO_DIRECTION = GPIO_DIR + "gpio" + POWER_LOSS_GPIO + "/direction"


class HWRebootCause(object):

    def __init__(self):
        pass

    def exec_cmd(self, cmd):
        status, output = subprocess.getstatusoutput(cmd)
        if status:
            print('Failed :' + cmd)
        return status, output

    @staticmethod
    def _get_command_result_pipe(cmd1, cmd2):
        try:
            rc, result = getstatusoutput_noshell_pipe(cmd1, cmd2)
            if rc != [0, 0]:
                raise RuntimeError("Failed to execute command {} {}, return code {}, {}".format(cmd1, cmd2, rc, result))

        except OSError as e:
            raise RuntimeError("Failed to execute command {} {} due to {}".format(cmd1, cmd2, repr(e)))

        return result

    def check_power_loss(self):
        if os.path.isfile(POWER_LOSS_GPIO_VALUE):
            hw_reboot_cause = '0'
            with open(POWER_LOSS_GPIO_VALUE, 'r') as f:
                hw_reboot_cause = f.read()
            print("hw_reboot_cause:"+str(hw_reboot_cause))
            return bool(hw_reboot_cause == '1')

        try:
            event_log = self._get_command_result_pipe(["ipmitool", "sel", "elist"], ["grep", 'AC lost | Asserted'])
            ac_lost_event = "1 | 01/01/2000 | 00:00:00 | Event log Initiated"  # Init event log string
            if len(event_log) > 0:
                ac_lost_event = event_log.split('\n')[-1].strip()
                print(ac_lost_event)

            event_log = self._get_command_result_pipe(["ipmitool", "sel", "elist"], ["grep", 'Power Supply AC lost | Deasserted'])
            power_off_deasserted_event = "1 | 01/01/2000 | 00:00:00 | Event log Initiated"  # Init event log string
            if len(event_log) > 0:
                power_off_deasserted_event = event_log.split('\n')[-1].strip()
                print(power_off_deasserted_event)

            event_log = self._get_command_result_pipe(["ipmitool", "sel", "elist"], ["grep", 'System Restart | Asserted'])
            sys_restart_event = "1 | 01/01/2000 | 00:00:00 | Event log Initiated"  # Init event log string
            if len(event_log) > 0:
                sys_restart_event = event_log.split('\n')[-1].strip()
                print(sys_restart_event)

            """126 | 04/27/2020 | 13:16:27 | Power Unit Power Unit | AC lost | Asserted"""
            ac_lost_event = ac_lost_event.split("|")
            ac_lost_order = int(ac_lost_event[0], 16)
            """2a70 | 02/17/2021 | 09:45:25 | Power Supply PSU_n Input lost | Power Supply AC lost | Deasserted"""
            power_off_deasserted_event = power_off_deasserted_event.split("|")
            power_off_deasserted_time = datetime.strptime(
                power_off_deasserted_event[1] + power_off_deasserted_event[2], ' %m/%d/%Y  %H:%M:%S ')

            """127 | 04/27/2020 | 13:16:26 | System Boot Initiated | System Restart | Asserted"""
            sys_restart_event = sys_restart_event.split("|")
            sys_restart_order = int(sys_restart_event[0], 16)
            sys_restart_time = datetime.strptime(
                sys_restart_event[1] + sys_restart_event[2], ' %m/%d/%Y  %H:%M:%S ')

        except Exception as error:
            print("check_power_loss failed: {} !".format(str(error)))
            return False

        with open(GPIO_EXPORT_PATH, 'w') as f:
            f.write(POWER_LOSS_GPIO + '\n')

        with open(POWER_LOSS_GPIO_DIRECTION, 'w') as f:
            f.write('out\n')

        order_diff = sys_restart_order - ac_lost_order
        power_off_time_diff = power_off_deasserted_time - sys_restart_time

        if order_diff == 1 or (power_off_time_diff.total_seconds() > -5 and power_off_time_diff.total_seconds() < 12):
            with open(POWER_LOSS_GPIO_VALUE, 'w') as f:
                f.write('1\n')
            return True
        else:
            with open(POWER_LOSS_GPIO_VALUE, 'w') as f:
                f.write('0\n')
            return False
