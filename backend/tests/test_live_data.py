import pytest
from app.services.live_data.null_provider import UnconfiguredLiveDataProvider
from app.services.live_data.base import LiveDataNotConfiguredError
from app.schemas.live_data import DataState


def test_unconfigured_live_data_provider_status():
    provider = UnconfiguredLiveDataProvider()
    status = provider.get_status()
    assert status.is_connected is False
    assert status.data_state == DataState.UNAVAILABLE
    assert "currently unavailable" in status.status_message


@pytest.mark.asyncio
async def test_unconfigured_live_data_provider_throws_on_fetch():
    provider = UnconfiguredLiveDataProvider()
    with pytest.raises(LiveDataNotConfiguredError):
        await provider.fetch_vehicle_positions()

    with pytest.raises(LiveDataNotConfiguredError):
        await provider.fetch_service_alerts()

    with pytest.raises(LiveDataNotConfiguredError):
        await provider.fetch_trip_updates()
