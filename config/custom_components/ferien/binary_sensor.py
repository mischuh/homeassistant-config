"""
Utilizes the api `ferien-api.de` to provide a binary sensor to indicate if
today is a german vacational day or not - based on your configured state.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.ferien/
"""

from collections import namedtuple
from datetime import datetime, timedelta
import logging
import requests

import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

REQUIREMENTS = ['requests==2.20.1']

_LOGGER = logging.getLogger(__name__)

ALL_STATE_CODES = [
    "BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", "NI", "NW", "RP", "SL",
    "SN", "ST", "SH", "TH"
]

ATTR_START = 'start'
ATTR_END = 'end'
ATTR_NEXT_START = 'next_start'
ATTR_NEXT_END = 'next_end'
ATTR_VACATION_NAME = 'vacation_name'

CONF_NAME_DEFAULT = 'Vacation Sensor'
CONF_STATE = 'state_code'

ICON_OFF_DEFAULT = 'mdi:calendar-remove'
ICON_ON_DEFAULT = 'mdi:calendar-check'

# Don't rush the api. Every 12h should suffice.
MIN_TIME_BETWEEN_UPDATES = timedelta(hours=12)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STATE): vol.In(ALL_STATE_CODES),
    vol.Optional(CONF_NAME, default=CONF_NAME_DEFAULT): cv.string
})

SCAN_INTERVAL = timedelta(minutes=1)


def setup_platform(hass, config, add_devices, discovery_info=None):
    state_code = config.get(CONF_STATE)
    name = config.get(CONF_NAME)

    try:
        init_data = VacationData.make_request(state_code)
    except Exception:
        raise PlatformNotReady()

    data_object = VacationData(init_data, state_code)
    add_devices([VacationSensor(name, data_object)], False)


class VacationSensor(BinarySensorDevice):
    """Implementation of the vacation sensor."""

    def __init__(self, name, data_object):
        self._name = name
        self.data_object = data_object
        self._state = None
        self._state_attrs = {}

    @property
    def name(self):
        """Returns the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return ICON_ON_DEFAULT if self.is_on else ICON_OFF_DEFAULT

    @property
    def is_on(self):
        """Returns the state of the device."""
        return self._state

    @property
    def device_state_attributes(self):
        """Returns the state attributes of this device."""
        return self._state_attrs

    @staticmethod
    def _get_current_vacation(vacs, dt=None):
        """Returns the current vacation based on the given dt.
        Returns None if no vacation sourrounds (start, end) the
        given dt."""
        dt = dt or datetime.now()
        res = [i for i in vacs if i.start <= dt <= i.end][-1:]
        if len(res) <= 0:
            return None
        return res[0]

    @staticmethod
    def _get_next_vacation(vacs, dt=None):
        dt = dt or datetime.now()
        res = sorted([i for i in vacs if i.start >= dt], key=lambda i: i.start)
        if len(res) <= 0:
            return None
        return res[0]

    def update(self):
        """Updates the state and state attributes."""
        self.data_object.update()
        vacs = self.data_object.data
        cur = self._get_current_vacation(vacs)
        if cur is None:
            self._state = False
            nextvac = self._get_next_vacation(vacs)
            if nextvac is None:
                self._state_attrs = {}
            else:
                self._state_attrs = {
                    ATTR_NEXT_START: nextvac.start.strftime('%Y-%m-%d'),
                    ATTR_NEXT_END: nextvac.end.strftime('%Y-%m-%d'),
                    ATTR_VACATION_NAME: nextvac.name
                }
        else:
            self._state = True
            self._state_attrs = {
                ATTR_START: cur.start.strftime('%Y-%m-%d'),
                ATTR_END: cur.end.strftime('%Y-%m-%d'),
                ATTR_VACATION_NAME: cur.name
            }


class VacationData:
    """Class for handling data retrieval."""

    API_URL = 'https://ferien-api.de/api/v1/holidays/{state_code}'

    """Internal representation of a vacation."""
    Item = namedtuple("Item", ["start", "end", "name", "state"])

    def __init__(self, initial_vacs, state_code):
        """Initializer."""
        self.state_code = str(state_code)
        self.data = self.convert(initial_vacs)

    @classmethod
    def make_request(cls, state_code):
        """Makes a request to the ferien-api.de using the given
        state_code."""
        resp = requests.get(cls.API_URL.format(state_code=state_code))
        if resp.status_code != 200:
            _LOGGER.error("ferien-api.de failed with http code = %s\n"
                          "Error: %s", resp.status_code, resp.text)
            raise RuntimeError("ferien-api.de failed")
        js = resp.json()
        return js

    @classmethod
    def convert(cls, raw):
        """Converts the ferien-api json to an internal model."""
        def _single(i):
            return cls.Item(
                start=datetime.strptime(i.get('start'), '%Y-%m-%dT%H:%M'),
                end=datetime.strptime(i.get('end'), '%Y-%m-%dT%H:%M'),
                name=i.get('name'),
                state=i.get('stateCode')
            )
        return [_single(i) for i in raw]

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Updates the publically available data container."""
        try:
            self.data = self.convert(self.make_request(self.state_code))
        except Exception:
            if self.data is None:
                raise
            _LOGGER.error("Failed to update the vacation data."
                          "Re-using an old state")