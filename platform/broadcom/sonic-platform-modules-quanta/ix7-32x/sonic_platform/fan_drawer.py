#!/usr/bin/env python

#############################################################################
# Quanta
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class FanDrawer(FanDrawerBase):

    def __init__(self, index, fan_list):
        FanDrawerBase.__init__(self)

        self._fan_list = fan_list
        self._index = index

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return 'Fantray{}'.format(self._index)

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        return self._fan_list[0].get_presence()

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

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self._fan_list[0].get_status()

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent
            device or -1 if cannot determine the position
        """
        return self._index

    def is_replaceable(self):
        """
        Indicate whether this Fandrawer is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True

    def set_status_led(self, color):
        """
        Set led to expected color
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if set success, False if fail.
        """
        # Leds are controlled by Smart-fussion FPGA.
        # Return True to avoid thermalctld alarm.
        return True

    def get_status_led(self):
        """
        Gets the state of the Fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if self.get_presence():
            if self.get_fan(0).get_status():
                return self.STATUS_LED_COLOR_GREEN
            else:
                return self.STATUS_LED_COLOR_RED
        else:
            return self.STATUS_LED_COLOR_OFF

    def get_maximum_consumed_power(self):
        """
        Retrives the maximum power drawn by Fan Drawer
        Returns:
            A float, with value of the maximum consumable power of the
            component.
        """
        return 0.0
