"""Test the Elexa Guardian sensors."""

from datetime import UTC, datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from homeassistant.components.guardian import CONF_UID, DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

UPTIME_MINUTES = 41
UPTIME_NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


@pytest.fixture
def uptime_now(freezer: FrozenDateTimeFactory) -> datetime:
    """Freeze time before the sensor platform is set up."""
    freezer.move_to(UPTIME_NOW)
    return UPTIME_NOW


@pytest.fixture(name="platforms")
def platforms_fixture(uptime_now: datetime) -> list[Platform]:
    """Load the sensor platform after time is frozen."""
    return [Platform.SENSOR]


async def test_valve_controller_uptime_is_absolute(
    hass: HomeAssistant,
    uptime_now: datetime,
    freezer: FrozenDateTimeFactory,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
    setup_guardian: None,
) -> None:
    """Uptime is the absolute boot time, stable across polls within a minute."""
    entity_id = entity_registry.async_get_entity_id(
        Platform.SENSOR, DOMAIN, f"{config_entry.data[CONF_UID]}_uptime"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.UPTIME
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    expected = (uptime_now - timedelta(minutes=UPTIME_MINUTES)).isoformat(
        timespec="seconds"
    )
    assert state.state == expected

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == expected
