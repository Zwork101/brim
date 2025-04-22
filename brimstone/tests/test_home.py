import asyncio
import time
import sys

from bs4 import BeautifulSoup
import pytest
from quart.typing import TestClientProtocol

@pytest.mark.asyncio
async def test_homepage(client: TestClientProtocol):
    resp = await client.get("/")
    assert resp.status_code == 200
    
@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_stats(client: TestClientProtocol):
    resp = await client.get("/stats")
    assert resp.status_code == 200
    
@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_stats"])
async def test_stats_version(client: TestClientProtocol):
    python_version = sys.implementation.name = ' ' + \
        f'{sys.implementation.version.major}.{sys.implementation.version.minor}.{sys.implementation.version.micro}'
    
    resp = await client.get("/stats")
    soup = BeautifulSoup(await resp.get_data(as_text=True), 'html.parser')
    
    first_p_tag = soup.select_one("p:first-of-type")
    assert first_p_tag
    assert python_version in first_p_tag.text

@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_stats"])
async def test_stats_uptime(client: TestClientProtocol):
    first_resp = await client.get("/stats")
    
    await asyncio.sleep(.25)
        
    second_resp = await client.get("/stats")
    
    first_soup = BeautifulSoup(await first_resp.get_data(True), 'html.parser')
    second_soup = BeautifulSoup(await second_resp.get_data(True), 'html.parser')
    
    first_count = first_soup.select_one("p:last-of-type")
    second_count = second_soup.select_one("p:last-of-type")
    
    assert first_count is not None and second_count is not None
    
    site_delay = float(second_count.text.split(" ")[2]) - float(first_count.text.split(" ")[2])
    
    assert site_delay <= .3  # Check for .25 difference with .05 room for error
