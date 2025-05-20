import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_MODEL,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_FIRMWARE,
    CONF_SERIAL_NUMBER,
    DOMAIN,
)
from .sensor_types.inverter import INVERTER_POWER_LIMIT
from .sensor_types.number_entity_description import GrowattNumberEntityDescription

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.data[CONF_SERIAL_NUMBER]]
    entities = []
    sensor_descriptions: list[GrowattNumberEntityDescription] = []

    # Add your number descriptions here (can be expanded later)
    sensor_descriptions.append(INVERTER_POWER_LIMIT)

    # Request the coordinator to track this register
    coordinator.get_keys_by_name({sensor.key for sensor in sensor_descriptions}, update_keys=True)

    entities.extend(
        [
            GrowattNumberEntity(
                coordinator, description=description, entry=config_entry
            )
            for description in sensor_descriptions
        ]
    )

    async_add_entities(entities, True)


class GrowattNumberEntity(CoordinatorEntity, NumberEntity):
    """Growatt number entity."""

    def __init__(self, coordinator, description, entry):
        super().__init__(coordinator, description.key)
        self.entity_description: GrowattNumberEntityDescription = description
        self._config_entry = entry

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_SERIAL_NUMBER])},
            manufacturer="Growatt",
            model=entry.data[CONF_MODEL],
            sw_version=entry.data[CONF_FIRMWARE],
            name=entry.options[CONF_NAME],
        )

    @property
    def native_value(self) -> int:
        return self.coordinator.data.get(self.entity_description.key, 0)

    async def async_set_native_value(self, value: float) -> None:
        raw_value = int(value)
        await self.coordinator.write_register(self.entity_description.register, raw_value)
        await self.coordinator.force_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update the HA state when coordinator has new data."""
        if (state := self.coordinator.data.get(self.entity_description.key)) is not None:
            self._attr_native_value = state
            self.async_write_ha_state()
