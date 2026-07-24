import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.modules.agents.editor_agent import EditorAgent
from backend.app.modules.automation.agents.capabilities.checker_video import ValidateVideoCapability

@pytest.mark.asyncio
async def test_editor_agent_execute():
    # Setup mock capabilities and subprocess
    with patch("backend.app.modules.agents.editor_agent.ai_client.generate", new_callable=AsyncMock) as mock_generate, \
         patch("backend.app.modules.agents.editor_agent.asyncio.create_subprocess_shell") as mock_subprocess, \
         patch("backend.app.modules.agents.editor_agent.ValidateVideoCapability.execute", new_callable=AsyncMock) as mock_checker:
        
        mock_generate.return_value = "export const MainComposition = () => null;"
        
        process_mock = AsyncMock()
        process_mock.communicate.return_value = (b"stdout", b"")
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock
        
        mock_qa_result = MagicMock()
        mock_qa_result.payload = {"scenes_matched": True, "titles_present": True, "branding_present": True, "visual_artifacts_detected": False, "issues": []}
        mock_checker.return_value = mock_qa_result
        
        agent = EditorAgent()
        
        # Test input data
        input_data = {
            "tenant_id": "test-tenant",
            "project_id": "test-project",
            "project_data": "some data",
            "script": "some script",
            "brief": "some brief"
        }
        
        # We don't need a real db session for memory since it's mocked or doesn't throw if company profile is not found
        # but let's mock memory anyway if needed, or pass None if it doesn't fail
        with patch.object(agent.memory, "get_company_profile", new_callable=AsyncMock) as mock_memory:
            mock_memory.return_value = {}
            
            result = await agent.execute(session=None, input_data=input_data)
            
            # Assertions
            assert result is not None
            assert "composition_code" in result
            assert "qa_report" in result
            assert result["qa_report"]["scenes_matched"] is True
            
            # Verify subprocess was called for rendering
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert "npx remotion render" in call_args
            
            # Verify checking capability was called
            mock_checker.assert_called_once()
            checker_args = mock_checker.call_args[1]["context"]
            assert "video_url" in checker_args
            assert "brief" in checker_args
