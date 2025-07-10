import asyncio
import os
import subprocess
import logging
from typing import Optional
from info import Config

logger = logging.getLogger(__name__)

class FFmpegProcessor:
    """FFmpeg video processor for various operations"""
    
    def __init__(self):
        self.ffmpeg_path = Config.FFMPEG_PATH
        self.ffprobe_path = Config.FFPROBE_PATH
    
    async def process_video(self, input_path: str, operation: str, process_id: str, progress_tracker=None) -> Optional[str]:
        """Process video based on operation type"""
        try:
            output_path = f"{Config.UPLOADS_DIR}/{process_id}_{operation}.mp4"
            
            # Select processing method based on operation
            if operation == "trim":
                return await self.trim_video(input_path, output_path, progress_tracker)
            elif operation == "compress":
                return await self.compress_video(input_path, output_path, progress_tracker)
            elif operation == "rotate":
                return await self.rotate_video(input_path, output_path, progress_tracker)
            elif operation == "mute":
                return await self.mute_video(input_path, output_path, progress_tracker)
            elif operation == "reverse":
                return await self.reverse_video(input_path, output_path, progress_tracker)
            elif operation == "extract_audio":
                return await self.extract_audio(input_path, output_path.replace('.mp4', '.mp3'), progress_tracker)
            elif operation == "screenshot":
                return await self.take_screenshot(input_path, output_path.replace('.mp4', '.jpg'), progress_tracker)
            elif operation == "watermark":
                return await self.add_watermark(input_path, output_path, progress_tracker)
            elif operation == "resolution":
                return await self.change_resolution(input_path, output_path, progress_tracker)
            elif operation == "replace_audio":
                return await self.replace_audio(input_path, output_path, progress_tracker)
            elif operation == "merge":
                return await self.merge_videos(input_path, output_path, progress_tracker)
            elif operation == "subtitles":
                return await self.add_subtitles(input_path, output_path, progress_tracker)
            else:
                logger.error(f"Unknown operation: {operation}")
                return None
                
        except Exception as e:
            logger.error(f"Error in process_video: {e}")
            return None
    
    async def trim_video(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Trim video to first 30 seconds"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', '0',
                '-t', '30',
                '-c', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error trimming video: {e}")
            return None
    
    async def compress_video(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Compress video to reduce file size"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vcodec', 'libx264',
                '-crf', '28',
                '-preset', 'fast',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error compressing video: {e}")
            return None
    
    async def rotate_video(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Rotate video 90 degrees clockwise"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', 'transpose=1',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error rotating video: {e}")
            return None
    
    async def mute_video(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Remove audio from video"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-an',
                '-c:v', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error muting video: {e}")
            return None
    
    async def reverse_video(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Reverse video playback"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', 'reverse',
                '-af', 'areverse',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error reversing video: {e}")
            return None
    
    async def extract_audio(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Extract audio from video"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vn',
                '-acodec', 'mp3',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    
    async def take_screenshot(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Take screenshot at 50% of video duration"""
        try:
            # Get video duration first
            duration = await self.get_video_duration(input_path)
            if not duration:
                duration = 10  # Default to 10 seconds
            
            screenshot_time = duration / 2
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', str(screenshot_time),
                '-vframes', '1',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def add_watermark(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Add text watermark to video"""
        try:
            from helpers.watermark import WatermarkProcessor
            watermark_processor = WatermarkProcessor()
            
            return await watermark_processor.add_text_watermark(
                input_path, 
                output_path, 
                "ꜰᴛᴍ ᴅᴇᴠᴇʟᴏᴘᴇʀᴢ",
                progress_tracker
            )
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return None
    
    async def change_resolution(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Change video resolution to 720p"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', 'scale=1280:720',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error changing resolution: {e}")
            return None
    
    async def replace_audio(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Replace audio with silence (as demo)"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error replacing audio: {e}")
            return None
    
    async def merge_videos(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Merge video with itself (as demo)"""
        try:
            # Create a temporary file list
            list_file = f"{Config.TEMP_DIR}/merge_list.txt"
            with open(list_file, 'w') as f:
                f.write(f"file '{input_path}'\n")
                f.write(f"file '{input_path}'\n")
            
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            
            # Clean up
            try:
                os.remove(list_file)
            except:
                pass
            
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error merging videos: {e}")
            return None
    
    async def add_subtitles(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Add hardcoded subtitle (as demo)"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', "drawtext=text='ᴘʀᴏᴄᴇssᴇᴅ ʙʏ ꜰᴛᴍ ᴅᴇᴠᴇʟᴏᴘᴇʀᴢ':fontsize=24:fontcolor=white:x=10:y=10",
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding subtitles: {e}")
            return None
    
    async def get_video_duration(self, input_path: str) -> Optional[float]:
        """Get video duration in seconds"""
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return float(stdout.decode().strip())
            else:
                logger.error(f"Error getting video duration: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_video_duration: {e}")
            return None
    
    async def _run_ffmpeg_command(self, cmd: list, progress_tracker=None) -> bool:
        """Run FFmpeg command with progress tracking"""
        try:
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Add progress reporting to FFmpeg command
            if '-progress' not in cmd:
                cmd.extend(['-progress', 'pipe:2'])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress in real-time
            if progress_tracker:
                asyncio.create_task(self._monitor_ffmpeg_progress(process, progress_tracker))
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("FFmpeg command completed successfully")
                return True
            else:
                logger.error(f"FFmpeg command failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error running FFmpeg command: {e}")
            return False
    
    async def _monitor_ffmpeg_progress(self, process, progress_tracker):
        """Monitor FFmpeg progress output"""
        try:
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                
                line = line.decode('utf-8').strip()
                
                # Parse progress information
                if line.startswith('out_time_ms='):
                    try:
                        time_ms = int(line.split('=')[1])
                        # This is a simplified progress calculation
                        # In real implementation, you'd need the total duration
                        # For now, simulate progress based on processing time
                        await asyncio.sleep(0.1)
                    except:
                        pass
                elif line.startswith('progress='):
                    status = line.split('=')[1]
                    if status == 'end':
                        break
                        
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg progress: {e}")
    
    def check_ffmpeg_installed(self) -> bool:
        """Check if FFmpeg is installed and accessible"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"FFmpeg not found: {e}")
            return False
