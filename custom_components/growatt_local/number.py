import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_MODEL,
    CONF_NAME,
    PERCENTAGE,
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
    coordinator = hass.data[DOMAIN][config_entry.data[CONF_NAME]]
    serial_number = config_entry.data[CONF_SERIAL_NUMBER]
    model = config_entry.data[CONF_MODEL]
    name = config_entry.data[CONF_NAME]
    firmware = config_entry.data[CONF_FIRMWARE]

    entities = [
        GrowattPowerLimitNumber(
            coordinator,
            serial_number,
            model,
            name,
            firmware,
            INVERTER_POWER_LIMIT
        )
    ]

    async_add_entities(entities)


class GrowattPowerLimitNumber(CoordinatorEntity, NumberEntity):
    def __init__(
        self,
        coordinator,
        serial_number: str,
        model: str,
        name: str,
        firmware: str,
        description: GrowattNumberEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{serial_number}_{description.key}"
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._serial_number = serial_number
        self._model = model
        self._name = name
        self._firmware = firmware

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=self._name,
            manufacturer="Growatt",
            model=self._model,
            sw_version=self._firmware,
        )

    @property
    def native_value(self) -> Optional[float]:
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.write_register(
            self.entity_description.register, int(value)
        )
        await self.coordinator.async_request_refresh()
