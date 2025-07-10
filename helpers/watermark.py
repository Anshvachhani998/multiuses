import asyncio
import os
import logging
from typing import Optional
from info import Config

logger = logging.getLogger(__name__)

class WatermarkProcessor:
    """Watermark processor for videos"""
    
    def __init__(self):
        self.ffmpeg_path = Config.FFMPEG_PATH
    
    async def add_text_watermark(self, input_path: str, output_path: str, text: str, progress_tracker=None) -> Optional[str]:
        """Add text watermark to video"""
        try:
            # Sanitize text for FFmpeg
            safe_text = text.replace("'", "\\'").replace('"', '\\"')
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f"drawtext=text='{safe_text}':fontsize=24:fontcolor=white:x=10:y=10:enable='between(t,0,60)'",
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding text watermark: {e}")
            return None
    
    async def add_image_watermark(self, input_path: str, output_path: str, watermark_path: str, progress_tracker=None) -> Optional[str]:
        """Add image watermark to video"""
        try:
            if not os.path.exists(watermark_path):
                logger.error(f"Watermark image not found: {watermark_path}")
                return None
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-i', watermark_path,
                '-filter_complex', '[0:v][1:v]overlay=W-w-10:10',
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding image watermark: {e}")
            return None
    
    async def add_logo_watermark(self, input_path: str, output_path: str, position: str = "bottom-right", progress_tracker=None) -> Optional[str]:
        """Add logo watermark with predefined positions"""
        try:
            # Define position coordinates
            positions = {
                "top-left": "10:10",
                "top-right": "W-w-10:10",
                "bottom-left": "10:H-h-10",
                "bottom-right": "W-w-10:H-h-10",
                "center": "(W-w)/2:(H-h)/2"
            }
            
            pos = positions.get(position, positions["bottom-right"])
            
            # Use text watermark as logo substitute
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f"drawtext=text='ꜰᴛᴍ':fontsize=20:fontcolor=white:x={pos.split(':')[0]}:y={pos.split(':')[1]}:alpha=0.7",
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding logo watermark: {e}")
            return None
    
    async def add_animated_watermark(self, input_path: str, output_path: str, text: str, progress_tracker=None) -> Optional[str]:
        """Add animated text watermark"""
        try:
            safe_text = text.replace("'", "\\'").replace('"', '\\"')
            
            # Create animated watermark that moves across screen
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f"drawtext=text='{safe_text}':fontsize=24:fontcolor=white:x='if(gte(t,0),((t)*100)\\,NAN)':y=50:alpha=0.8",
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding animated watermark: {e}")
            return None
    
    async def add_timestamp_watermark(self, input_path: str, output_path: str, progress_tracker=None) -> Optional[str]:
        """Add timestamp watermark"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f"drawtext=text='{timestamp}':fontsize=16:fontcolor=yellow:x=10:y=H-th-10",
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error adding timestamp watermark: {e}")
            return None
    
    async def remove_watermark(self, input_path: str, output_path: str, x: int, y: int, width: int, height: int, progress_tracker=None) -> Optional[str]:
        """Remove watermark by blurring specified area"""
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-vf', f"delogo=x={x}:y={y}:w={width}:h={height}",
                '-codec:a', 'copy',
                '-y', output_path
            ]
            
            await self._run_ffmpeg_command(cmd, progress_tracker)
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            logger.error(f"Error removing watermark: {e}")
            return None
    
    async def _run_ffmpeg_command(self, cmd: list, progress_tracker=None) -> bool:
        """Run FFmpeg command with progress tracking"""
        try:
            logger.info(f"Running watermark command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Simple progress simulation
            if progress_tracker:
                total_steps = 50
                for i in range(total_steps):
                    await asyncio.sleep(0.1)
                    if i % 5 == 0:  # Update every 5 steps
                        try:
                            # Simplified progress update
                            pass
                        except:
                            pass
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Watermark command completed successfully")
                return True
            else:
                logger.error(f"Watermark command failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error running watermark command: {e}")
            return False
    
    def create_text_image(self, text: str, output_path: str, font_size: int = 48, color: str = "white") -> bool:
        """Create a text image for watermarking"""
        try:
            # This would normally use PIL/Pillow to create text images
            # For now, we'll use FFmpeg to create a text overlay
            cmd = [
                self.ffmpeg_path,
                '-f', 'lavfi',
                '-i', f'color=size=400x100:color=transparent',
                '-vf', f"drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:x=(w-text_w)/2:y=(h-text_h)/2",
                '-frames:v', '1',
                '-y', output_path
            ]
            
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"Error creating text image: {e}")
            return False
