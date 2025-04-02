import pytest
import pickle
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from api.schemas.sniffer import SniffDetails, StartSniffDetails, SniffStatus
from api.repository.redis_repository import RedisRepository


@pytest.fixture
def mock_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock()
    redis_mock.set = AsyncMock()
    redis_mock.keys = AsyncMock(return_value=[])
    return redis_mock


@pytest.fixture
def repository(mock_redis):
    return RedisRepository(mock_redis)


@pytest.mark.asyncio
async def test_save_sniff(repository, mock_redis):
    sniff_id = uuid4()
    details = StartSniffDetails(interface="eth0", sniff_id=sniff_id, start_at=datetime.now())

    await repository.save_sniff(details)

    mock_redis.set.assert_called_once()
    key, value = mock_redis.set.call_args[0]
    assert key == str(sniff_id)
    assert isinstance(pickle.loads(value), SniffDetails)


@pytest.mark.asyncio
async def test_update_sniff(repository, mock_redis):
    sniff_id = uuid4()
    sniff_details = SniffDetails(interface="eth0", sniff_id=sniff_id, start_at=datetime.now(),
                                 status=SniffStatus.Running)

    mock_redis.get.return_value = pickle.dumps(sniff_details)
    new_status = SniffStatus.Stopped

    await repository.update_sniff(sniff_id, new_status)

    mock_redis.set.assert_called_once()
    updated_sniff = pickle.loads(mock_redis.set.call_args[0][1])
    assert updated_sniff.status == new_status


@pytest.mark.asyncio
async def test_get_sniff(repository, mock_redis):
    sniff_id = uuid4()
    expected_sniff = SniffDetails(interface="eth0", sniff_id=sniff_id, start_at=datetime.now(),
                                  status=SniffStatus.Running)

    mock_redis.get.return_value = pickle.dumps(expected_sniff)

    result = await repository.get_sniff(sniff_id)

    assert result == expected_sniff


@pytest.mark.asyncio
async def test_get_by_status(repository, mock_redis):
    sniff1 = SniffDetails(interface="eth0", sniff_id=uuid4(), start_at=datetime.now(), status=SniffStatus.Running)
    sniff2 = SniffDetails(interface="wlan0", sniff_id=uuid4(), start_at=datetime.now(), status=SniffStatus.Stopped)

    mock_redis.keys.return_value = ["key1", "key2"]
    mock_redis.get.side_effect = [pickle.dumps(sniff1), pickle.dumps(sniff2)]

    result = await repository.get_by_status(SniffStatus.Running)

    assert len(result) == 1
    assert result[0].status == SniffStatus.Running


@pytest.mark.asyncio
async def test_is_sniffer_running(repository, mock_redis):
    sniff1 = SniffDetails(interface="eth0", sniff_id=uuid4(), start_at=datetime.now(), status=SniffStatus.Running)

    mock_redis.keys.return_value = ["key1"]
    mock_redis.get.return_value = pickle.dumps(sniff1)

    result = await repository.is_sniffer_running("eth0")

    assert result is True

