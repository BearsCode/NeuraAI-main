import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.modules.agents.timelapse_agent import TimelapseAgent

@pytest.mark.asyncio
async def test_timelapse_agent_assemble_final():
    # Setup mock capabilities and subprocess
    with patch("backend.app.modules.agents.timelapse_agent.asyncio.create_subprocess_shell") as mock_subprocess, \
         patch("backend.app.modules.agents.timelapse_agent.storage_client.upload_from_url", new_callable=AsyncMock) as mock_upload, \
         patch("backend.app.modules.agents.timelapse_agent.storage_client.store_bytes", new_callable=AsyncMock) as mock_store:
         
        process_mock = AsyncMock()
        process_mock.communicate.return_value = (b"stdout", b"")
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock
        
        mock_store.return_value = ("internal_path", "http://uploaded.url/video.mp4")
        mock_upload.return_value = "http://uploaded.url/video.mp4"
        
        agent = TimelapseAgent()
        
        # Test assemble_final logic specifically
        # Mock httpx to prevent real downloads
        with patch("backend.app.modules.agents.timelapse_agent.httpx.AsyncClient") as mock_httpx_class:
            mock_client = AsyncMock()
            mock_httpx_class.return_value.__aenter__.return_value = mock_client
            
            mock_resp = MagicMock()
            mock_resp.content = b"fake video data"
            mock_client.get.return_value = mock_resp
            
            # mock os.path.exists to return true for out_file_path
            with patch("backend.app.modules.agents.timelapse_agent.os.path.exists", return_value=True):
                urls = ["http://example.com/clip1.mp4", "http://example.com/clip2.mp4"]
                final_path = await agent.assemble_final(urls)
                
                assert final_path is not None
                assert "output.mp4" in final_path
                
                # Check subprocess was called with ffmpeg
                mock_subprocess.assert_called_once()
                call_args = mock_subprocess.call_args[0][0]
                assert "ffmpeg" in call_args
                assert "concat" in call_args

@pytest.mark.asyncio
async def test_timelapse_agent_execute():
    with patch("backend.app.modules.agents.timelapse_agent.TimelapseAgent.analyze_project", new_callable=AsyncMock) as m_analyze, \
         patch("backend.app.modules.agents.timelapse_agent.TimelapseAgent.build_stages", new_callable=AsyncMock) as m_stages, \
         patch("backend.app.modules.agents.timelapse_agent.TimelapseAgent.plan_camera", new_callable=AsyncMock) as m_camera, \
         patch("backend.app.modules.agents.timelapse_agent.TimelapseAgent.generate_scenes", new_callable=AsyncMock) as m_scenes, \
         patch("backend.app.modules.agents.timelapse_agent.TimelapseAgent.assemble_final", new_callable=AsyncMock) as m_assemble, \
         patch("backend.app.modules.agents.timelapse_agent.storage_client.store_bytes", new_callable=AsyncMock) as mock_store:
         
         m_analyze.return_value = "construction"
         m_stages.return_value = []
         m_camera.return_value = {"stages": []}
         m_scenes.return_value = ["http://clip1.mp4"]
         
         # mock assemble returning local path
         m_assemble.return_value = "/tmp/fake_output.mp4"
         mock_store.return_value = ("internal", "http://final.url/video.mp4")
         
         agent = TimelapseAgent()
         
         with patch("backend.app.modules.agents.timelapse_agent.os.path.exists", return_value=True), \
              patch("backend.app.modules.agents.timelapse_agent.open", MagicMock()), \
              patch("backend.app.modules.agents.timelapse_agent.os.remove", MagicMock()):
              
              input_data = {"tenant_id": "test", "project_id": "test"}
              with patch.object(agent.memory, "get_company_profile", new_callable=AsyncMock) as mock_memory:
                  mock_memory.return_value = {}
                  result = await agent.execute(session=None, input_data=input_data)
                  
                  assert result["video_url"] == "http://final.url/video.mp4"
                  assert result["process_type"] == "construction"
                  mock_store.assert_called_once()
