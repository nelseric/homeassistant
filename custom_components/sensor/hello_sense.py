"""Component for the hello.is Sense sleep tracker."""

import logging
import json

import voluptuous as vol
from datetime import timedelta
import requests

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_API_KEY, STATE_UNKNOWN, TEMP_CELSIUS)

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
})

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""

    api_key = config.get(CONF_API_KEY)

    sense = HelloSenseData(api_key)
    sense.update()

    if sense.data is None:
        _LOGGER.error('Unable to fetch REST data')
        return False

    add_devices(HelloSenseSensor(sense, stream)
                for stream in sense.streams)


class HelloSenseSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sense, stream):
        self.sense = sense
        self.stream = stream
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Hello Sense: ' + self.stream

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state['value']

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._state['unit'] == 'c':
            return TEMP_CELSIUS
        return self._state['unit']

    @property
    def state_attributes(self):
        return self._state

    def update(self):
        """Get the latest data from REST API and update the state."""
        self.sense.update()
        value = self.sense.data[self.stream]

        if value is None:
            value = STATE_UNKNOWN

        self._state = value


class HelloSenseData(object):

    def __init__(self, api_key):
        """Initialize the data object."""
        headers = {  # Headers
            'Authorization': 'Bearer %s' % api_key,
            'User-Agent': 'Sense/1.4.4.4 Platform/iOS OS/9.3.2"',
            'X-Client-Version': '1.4.4.4"'
        }
        self._request = requests.Request(
            'GET', 'https://api.hello.is/v1/room/current', headers=headers
        ).prepare()

        self.streams = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from REST service with provided method."""
        try:
            with requests.Session() as sess:
                response = sess.send(
                    self._request, timeout=10, verify=True)
            self.data = json.loads(response.text)
            self.streams = self.data.keys()
        except requests.exceptions.RequestException:
            _LOGGER.error("Error fetching data: %s", self._request)
            self.data = None
        except json.JSONDecodeError:
            _LOGGER.error("Error parsing data: %s", self._request)
            self.data = None
