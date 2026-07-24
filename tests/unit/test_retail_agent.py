import os
import pytest
import pandas as pd
import yaml
from tempfile import NamedTemporaryFile
from backend.app.modules.agents.retail_agent import RetailAgent

@pytest.fixture
def agent():
    return RetailAgent()

@pytest.mark.asyncio
async def test_process_catalog_file_csv_success(agent):
    df = pd.DataFrame({
        "Name": ["Product 1", "Product 2"],
        "Цена": ["100,50", "200"],
        "Категория": ["Cat 1", "Cat 2"],
        "Description": ["Desc 1", "Desc 2"]
    })
    with NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df.to_csv(f.name, index=False)
        filepath = f.name
        
    try:
        result = await agent.process_catalog_file(filepath, "csv")
        assert result["status"] == "success"
        assert result["imported_count"] == 2
        assert result["error_count"] == 0
        items = result["items"]
        assert items[0]["name"] == "Product 1"
        assert items[0]["price"] == 100.50
        assert items[0]["category"] == "Cat 1"
        assert items[0]["description"] == "Desc 1"
    finally:
        os.remove(filepath)

@pytest.mark.asyncio
async def test_process_catalog_file_yaml_success(agent):
    data = {
        "items": [
            {"название": "YML Product", "price": 500.0, "category": "YML Cat"}
        ]
    }
    with NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        yaml.dump(data, f)
        filepath = f.name
        
    try:
        result = await agent.process_catalog_file(filepath, "yaml")
        assert result["status"] == "success"
        assert result["imported_count"] == 1
        assert result["error_count"] == 0
        assert result["items"][0]["name"] == "YML Product"
        assert result["items"][0]["price"] == 500.0
    finally:
        os.remove(filepath)

@pytest.mark.asyncio
async def test_process_catalog_file_missing_columns(agent):
    df = pd.DataFrame({
        "Unknown": ["A"],
        "Random": ["B"]
    })
    with NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df.to_csv(f.name, index=False)
        filepath = f.name
        
    try:
        result = await agent.process_catalog_file(filepath, "csv")
        assert result["status"] == "error"
        assert "Missing required columns" in result["error"]
    finally:
        os.remove(filepath)

@pytest.mark.asyncio
async def test_process_catalog_file_not_found(agent):
    result = await agent.process_catalog_file("/non/existent/path.csv", "csv")
    assert result["status"] == "error"
    assert "File not found" in result["error"]

@pytest.mark.asyncio
async def test_process_catalog_file_invalid_format(agent):
    with NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("test")
        filepath = f.name
        
    try:
        result = await agent.process_catalog_file(filepath, "unknown")
        assert result["status"] == "error"
        assert "Unsupported format" in result["error"]
    finally:
        os.remove(filepath)

@pytest.mark.asyncio
async def test_process_catalog_file_empty_name(agent):
    # pandas writes empty strings as missing/nan by default in csv
    # We will explicitly leave the first name blank
    df = pd.DataFrame({
        "Name": ["", "Valid"],
        "Price": [10, 20]
    })
    with NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        df.to_csv(f.name, index=False)
        filepath = f.name
        
    try:
        result = await agent.process_catalog_file(filepath, "csv")
        assert result["status"] == "success"
        assert result["imported_count"] == 1
        assert result["error_count"] == 1
        assert "Empty name" in result["errors"][0]["error"]
    finally:
        os.remove(filepath)
