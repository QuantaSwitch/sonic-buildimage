#!/usr/bin/env python

########################################################################
# Quanta IX7
#
# Name: component.py, version: 1.3
# Module contains an implementation of SONiC Platform Base API and
# provides the Components' (e.g., BIOS, CPLD, FPGA, etc.) available in
# the platform
#
########################################################################

try:
    import subprocess
    from sonic_platform_base.component_base import ComponentBase
    from collections import namedtuple
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Component(ComponentBase):
    def __init__(self):
        ComponentBase.__init__(self)
        self.name = None
        self.description = None

    def get_name(self):
        return self.name

    def get_model(self):
        """
        Retrieves the part number of the component
        Returns:
            string: Part number of component
        """
        return 'N/A'

    def get_serial(self):
        """
        Retrieves the serial number of the component
        Returns:
            string: Serial number of component
        """
        return 'N/A'

    def get_presence(self):
        """
        Retrieves the presence of the component
        Returns:
            bool: True if  present, False if not
        """
        return True

    def get_status(self):
        """
        Retrieves the operational status of the component
        Returns:
            bool: True if component is operating properly, False if not
        """
        return True

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent
            device or -1 if cannot determine the position
        """
        return -1

    def is_replaceable(self):
        """
        Indicate whether component is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return False

    def get_description(self):
        return self.description

    def get_available_firmware_version(self, image_path):
        """
        Retrieves the available firmware version of the component
        Note: the firmware version will be read from image
        Args:
            image_path: A string, path to firmware image
        Returns:
            A string containing the available firmware version of the component
        """
        return "N/A"

    def get_firmware_update_notification(self, image_path):
        """
        Retrieves a notification on what should be done in order to complete
        the component firmware update
        Args:
            image_path: A string, path to firmware image
        Returns:
            A string containing the component firmware update notification if required.
            By default 'None' value will be used, which indicates that no actions are required
        """
        return "None"

    def update_firmware(self, image_path):
        """
        Updates firmware of the component
        This API performs firmware update: it assumes firmware installation and loading in a single call.
        In case platform component requires some extra steps (apart from calling Low Level Utility)
        to load the installed firmware (e.g, reboot, power cycle, etc.) - this will be done automatically by API
        Args:
            image_path: A string, path to firmware image
        Raises:
            RuntimeError: update failed
        """
        return False

    def install_firmware(self, image_path):
        """
        Installs firmware to the component

        Args:
            image_path: A string, path to firmware image

        Returns:
            A boolean, True if install was successful, False if not
        """
        return False

    @staticmethod
    def _get_command_result(cmdline):
        try:
            proc = subprocess.Popen(cmdline,
                                    stdout=subprocess.PIPE,
                                    shell=True, stderr=subprocess.STDOUT,
                                    universal_newlines=True)
            stdout = proc.communicate()[0]
            rc = proc.wait()
            result = stdout.rstrip('\n')
            if rc != 0:
                raise RuntimeError("Failed to execute command {}, return code {}, {}".format(cmdline, rc, stdout))

        except OSError as e:
            raise RuntimeError("Failed to execute command {} due to {}".format(cmdline, repr(e)))

        return result


class ComponentBIOS(Component):
    COMPONENT_NAME = 'BIOS'
    COMPONENT_DESCRIPTION = 'BIOS - Basic Input/Output System'

    BIOS_QUERY_VERSION_COMMAND = "dmidecode -s bios-version"

    def __init__(self):
        super(ComponentBIOS, self).__init__()

        self.name = self.COMPONENT_NAME
        self.description = self.COMPONENT_DESCRIPTION

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        bios_ver = self._get_command_result(self.BIOS_QUERY_VERSION_COMMAND)
        if not bios_ver:
            return 'ERR'
        else:
            return bios_ver


class ComponentBMC(Component):
    COMPONENT_NAME = 'BMC'
    COMPONENT_DESCRIPTION = 'BMC - Board Management Controller'
    BMC_QUERY_VERSION_COMMAND = "ipmitool mc info | grep 'Firmware Revision'"

    def __init__(self):
        super(ComponentBMC, self).__init__()

        self.name = self.COMPONENT_NAME
        self.description = self.COMPONENT_DESCRIPTION

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        bmc_ver = self._get_command_result(self.BMC_QUERY_VERSION_COMMAND)
        if not bmc_ver:
            return 'ERR'
        else:
            bmc_ver = bmc_ver.split(": ")[1]
            return bmc_ver.strip()


class ComponentCPLD(Component):
    Cpld = namedtuple("Cpld", ['name', 'cmd_index', 'description'])

    cplds = {
        1: Cpld("UART_CPLD", 1, "UART"),
        2: Cpld("BOOT_CPLD", 2, "Power sequence"),
        3: Cpld("FAN_CPLD", 3, "Fan"),
        4: Cpld("MB_CPLD_IO_1", 5, "Port IO-1"),
        5: Cpld("MB_CPLD_IO_2", 6, "Port IO-2"),
        6: Cpld("MB_CPLD_LED_1", 4, "Port LED-1"),
        7: Cpld("MB_CPLD_LED_2", 7, "Port LED-2"),
    }

    def __init__(self, component_index):
        super(ComponentCPLD, self).__init__()
        self.index = component_index

    def get_name(self):
        """
        Retrieves the name of the component

        Returns:
            A string containing the name of the component
        """
        self.name = self.cplds[self.index].name

        return self.name

    def get_description(self):
        """
        Retrieves the description of the component

        Returns:
            A string containing the description of the component
        """
        self.description = self.cplds[self.index].description

        return self.description

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        res = self._get_command_result("ipmitool raw 0x32 0xff 0x02 {}".format(self.cplds[self.index].cmd_index))
        if not res:
            return 'ERR'
        else:
            return res.split()[3].upper() + res.split()[2].upper() + res.split()[1].upper() + res.split()[0].upper()

    @classmethod
    def get_component_list(cls):
        component_list = []
        cpld_number = len(cls.cplds)

        for cpld_idx in range(1, cpld_number + 1):
            component_list.append(cls(cpld_idx))

        return component_list


class ComponentPCIE(Component):
    COMPONENT_NAME = 'PCIe'
    COMPONENT_DESCRIPTION = 'ASIC PCIe Firmware'
    PCIE_QUERY_VERSION_COMMAND = "bcmcmd 'pciephy fw version' | grep 'FW version'"

    def __init__(self):
        super(ComponentPCIE, self).__init__()

        self.name = self.COMPONENT_NAME
        self.description = self.COMPONENT_DESCRIPTION

    def get_firmware_version(self):
        """
        Retrieves the firmware version of the component

        Returns:
            A string containing the firmware version of the component
        """
        version = self._get_command_result(self.PCIE_QUERY_VERSION_COMMAND)
        if not version:
            return 'ERR'
        else:
            version = version.split(": ")[1]
            return version.strip()
