from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Any

import httpx

from backend.app.core.configs import settings
from backend.app.integrations import storage_client

logger = logging.getLogger(__name__)


class VideoProcessingService:
    async def generate_subtitles(self, audio_url: str) -> list[dict[str, Any]]:
        if not settings.openai_api_key:
            logger.info("whisper_disabled_no_api_key")
            return [{"start": 0, "end": 5, "text": "Subtitles unavailable"}]

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            audio_response = await client.get(audio_url)
            if audio_response.status_code != 200:
                logger.error("audio_download_failed", extra={"url": audio_url})
                return []

            audio_data = audio_response.content
            files = {"file": ("audio.mp4", audio_data, "audio/mp4")}
            data = {
                "model": "whisper-1",
                "response_format": "verbose_json",
                "language": "ru",
            }

            whisper_response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )

            if whisper_response.status_code != 200:
                logger.error("whisper_api_error", extra={"status": whisper_response.status_code})
                return []

            result = whisper_response.json()
            segments = result.get("segments", [])
            return [
                {
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": seg.get("text", "").strip(),
                }
                for seg in segments
            ]

    async def burn_subtitles(
        self,
        video_url: str,
        subtitles: list[dict[str, Any]],
        output_format: str = "mp4",
    ) -> str:
        if not subtitles:
            logger.info("no_subtitles_to_burn")
            return video_url

        srt_content = self._subtitles_to_srt(subtitles)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".srt", delete=False, encoding="utf-8"
        ) as srt_file:
            srt_file.write(srt_content)
            srt_path = srt_file.name

        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, "input.mp4")
        output_path = os.path.join(tmp_dir, f"output.{output_format}")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                video_response = await client.get(video_url)
                if video_response.status_code != 200:
                    logger.error("video_download_failed", extra={"url": video_url})
                    return video_url

                with open(input_path, "wb") as f:
                    f.write(video_response.content)

            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-vf", f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=16,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1'",
                "-c:a", "aac",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-y",
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error("ffmpeg_error", extra={"stderr": stderr.decode()[:500]})
                return video_url

            with open(output_path, "rb") as f:
                video_data = f.read()

            _, stored_url = await storage_client.store_bytes(
                project_id="video_processing",
                file_name=f"processed/{os.path.basename(output_path)}",
                content_type="video/mp4",
                data=video_data,
            )
            return stored_url or video_url

        except FileNotFoundError:
            logger.warning("ffmpeg_not_found_returning_original_video")
            return video_url
        except Exception as exc:
            logger.error("video_processing_error", extra={"error": str(exc)})
            return video_url
        finally:
            for path in [srt_path, input_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass
            try:
                os.rmdir(tmp_dir)
            except Exception:
                pass

    async def normalize_video(
        self,
        video_url: str,
        target_width: int = 1080,
        target_height: int = 1920,
    ) -> str:
        tmp_dir = tempfile.mkdtemp()
        input_path = os.path.join(tmp_dir, "input.mp4")
        output_path = os.path.join(tmp_dir, "output.mp4")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                video_response = await client.get(video_url)
                if video_response.status_code != 200:
                    return video_url
                with open(input_path, "wb") as f:
                    f.write(video_response.content)

            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2",
                "-c:a", "aac",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-y",
                output_path,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                return video_url

            with open(output_path, "rb") as f:
                video_data = f.read()

            _, stored_url = await storage_client.store_bytes(
                project_id="video_processing",
                file_name=f"normalized/{os.path.basename(output_path)}",
                content_type="video/mp4",
                data=video_data,
            )
            return stored_url or video_url

        except FileNotFoundError:
            logger.warning("ffmpeg_not_found_returning_original")
            return video_url
        except Exception as exc:
            logger.error("normalize_video_error", extra={"error": str(exc)})
            return video_url
        finally:
            for path in [input_path, output_path]:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception:
                    pass
            try:
                os.rmdir(tmp_dir)
            except Exception:
                pass

    def _subtitles_to_srt(self, subtitles: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for i, sub in enumerate(subtitles, 1):
            start = self._seconds_to_srt_time(sub.get("start", 0))
            end = self._seconds_to_srt_time(sub.get("end", 0))
            text = sub.get("text", "")
            lines.append(str(i))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)

    def _seconds_to_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


video_processing = VideoProcessingService()
