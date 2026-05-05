from unittest.mock import AsyncMock

import pytest

from models import EmergencyStatus
from services import dispatch_emergency, resolve_emergency


@pytest.mark.asyncio
async def test_dispatch_raises_if_not_found():
    mock_db = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError, match="not found"):
        await dispatch_emergency(99999, mock_db)


@pytest.mark.asyncio
async def test_dispatch_returns_empty_if_not_pending():
    mock_emergency = AsyncMock()
    mock_emergency.status = EmergencyStatus.DISPATCHED

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_emergency
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await dispatch_emergency(1, mock_db)
    assert result == []


@pytest.mark.asyncio
async def test_resolve_returns_false_if_already_resolved():
    mock_emergency = AsyncMock()
    mock_emergency.status = EmergencyStatus.RESOLVED

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_emergency
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await resolve_emergency(1, mock_db)
    assert result is False
