import os
import re
import asyncio
import subprocess
import shlex
from utils import convert_to_bytes
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



async def manual_download_with_progress(url, output_path, label, queue):
    output_dir = os.path.dirname(output_path)
    output_file = os.path.basename(output_path)

    cmd = f"aria2c --dir={output_dir} --out={output_file} --max-connection-per-server=16 --split=16 --min-split-size=1M --console-log-level=warn --summary-interval=1 {shlex.quote(url)}"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    async for line in process.stdout:
        line = line.decode("utf-8").strip()
        match = re.search(r'(\d+(?:\.\d+)?)([KMG]?i?B)/(\d+(?:\.\d+)?)([KMG]?i?B)', line)
        if match:
            downloaded = convert_to_bytes(float(match.group(1)), match.group(2))
            total = convert_to_bytes(float(match.group(3)), match.group(4))

            await queue.put((downloaded, total, label))

    await process.wait()
