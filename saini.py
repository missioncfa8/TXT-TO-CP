import os
import re
import time
import mmap
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures
from math import ceil
from utils import progress_bar
from pyrogram import Client, filters
from pyrogram.types import Message
from io import BytesIO
from pathlib import Path  
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

def sanitize_filename(filename):
    """Sanitize filename to remove problematic characters"""
    # Remove or replace problematic characters including square brackets
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f\[\]]', '', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Strip leading/trailing whitespace
    filename = filename.strip()
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    # Limit filename length (keeping space for extension)
    if len(filename) > 150:
        filename = filename[:150]
    return filename

def duration(filename):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30)  # Add timeout to prevent hanging
        # Handle case where ffprobe fails to get duration
        duration_str = result.stdout.decode().strip()
        if duration_str and not duration_str.startswith('N/A'):
            # Make sure we can convert to float
            try:
                return float(duration_str)
            except ValueError:
                return 0.0  # Return default duration if conversion fails
        else:
            return 0.0  # Return default duration if not available
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, UnicodeDecodeError):
        return 0.0  # Return default duration if any error occurs

def get_mps_and_keys(api_url):
    try:
        response = requests.get(api_url, timeout=15)  # Increase timeout
        response.raise_for_status()  # Raise an exception for bad status codes
        response_json = response.json()
        mpd = response_json.get('mpd_url')
        keys = response_json.get('keys')
        return mpd, keys
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, etc.
        print(f"Error fetching data from API: {str(e)}")
        return None, None
    except ValueError as e:
        # Handle JSON decode errors
        print(f"Error decoding JSON response: {str(e)}")
        return None, None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected error in get_mps_and_keys: {str(e)}")
        return None, None
   
def exec(cmd):
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=300)
        output = process.stdout.decode()
        error = process.stderr.decode()
        print(f"Command: {cmd}")
        print(f"Output: {output}")
        if error:
            print(f"Error: {error}")
        return output
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return ""
    except Exception as e:
        print(f"Error executing command {cmd}: {str(e)}")
        return ""

def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec, cmds)

async def aio(url, name):
    k = f'{name}.pdf'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(k, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
        return k
    except Exception as e:
        print(f"Error in aio function: {str(e)}")
        return k

async def download(url, name):
    ka = f'{name}.pdf'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(ka, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
        return ka
    except Exception as e:
        print(f"Error in download function: {str(e)}")
        return ka

async def pdf_download(url, file_name, chunk_size=1024 * 10):
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
        r = requests.get(url, allow_redirects=True, stream=True, timeout=30)
        with open(file_name, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fd.write(chunk)
        return file_name
    except Exception as e:
        print(f"Error in pdf_download function: {str(e)}")
        return file_name

def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info

def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({f'{i[2]}':f'{i[0]}'})
            except:
                pass
    return new_info

async def decrypt_and_merge_video(mpd_url, keys_string, output_path, output_name, quality="720"):
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        cmd1 = f'yt-dlp -f "bv[height<={quality}]+ba/b" -o "{output_path}/file.%(ext)s" --allow-unplayable-format --no-check-certificate --external-downloader aria2c "{mpd_url}"'
        print(f"Running command: {cmd1}")
        result = subprocess.run(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        print(f"Command output: {result.stdout.decode()}")
        if result.stderr:
            print(f"Command error: {result.stderr.decode()}")

        avDir = list(output_path.iterdir())
        print(f"Downloaded files: {avDir}")
        print("Decrypting")

        video_decrypted = False
        audio_decrypted = False

        for data in avDir:
            if data.suffix == ".mp4" and not video_decrypted:
                cmd2 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/video.mp4"'
                print(f"Running command: {cmd2}")
                result = subprocess.run(cmd2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
                print(f"Command output: {result.stdout.decode()}")
                if result.stderr:
                    print(f"Command error: {result.stderr.decode()}")
                if (output_path / "video.mp4").exists():
                    video_decrypted = True
                data.unlink()
            elif data.suffix == ".m4a" and not audio_decrypted:
                cmd3 = f'mp4decrypt {keys_string} --show-progress "{data}" "{output_path}/audio.m4a"'
                print(f"Running command: {cmd3}")
                result = subprocess.run(cmd3, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
                print(f"Command output: {result.stdout.decode()}")
                if result.stderr:
                    print(f"Command error: {result.stderr.decode()}")
                if (output_path / "audio.m4a").exists():
                    audio_decrypted = True
                data.unlink()

        if not video_decrypted or not audio_decrypted:
            raise FileNotFoundError("Decryption failed: video or audio file not found.")

        cmd4 = f'ffmpeg -i "{output_path}/video.mp4" -i "{output_path}/audio.m4a" -c copy "{output_path}/{output_name}.mp4"'
        print(f"Running command: {cmd4}")
        result = subprocess.run(cmd4, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        print(f"Command output: {result.stdout.decode()}")
        if result.stderr:
            print(f"Command error: {result.stderr.decode()}")
            
        if (output_path / "video.mp4").exists():
            (output_path / "video.mp4").unlink()
        if (output_path / "audio.m4a").exists():
            (output_path / "audio.m4a").unlink()
        
        filename = output_path / f"{output_name}.mp4"

        if not filename.exists():
            raise FileNotFoundError("Merged video file not found.")

        return str(filename)

    except subprocess.TimeoutExpired:
        print("Process timed out during decryption and merging")
        raise
    except Exception as e:
        print(f"Error during decryption and merging: {str(e)}")
        raise

async def run(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        try:
            # Use asyncio.wait_for to implement timeout
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            print(f"Command timed out: {cmd}")
            return False

        print(f'[{cmd!r} exited with {proc.returncode}]')
        if proc.returncode == 1:
            return False
        if stdout:
            return f'[stdout]\n{stdout.decode()}'
        if stderr:
            return f'[stderr]\n{stderr.decode()}'
    except Exception as e:
        print(f"Error running command {cmd}: {str(e)}")
        return False

def old_download(url, file_name, chunk_size = 1024 * 10):
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
        r = requests.get(url, allow_redirects=True, stream=True, timeout=30)
        with open(file_name, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fd.write(chunk)
        return file_name
    except Exception as e:
        print(f"Error in old_download function: {str(e)}")
        return file_name

def human_readable_size(size, decimal_places=2):
    unit = 'B'
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"

async def download_video(url, cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    global failed_counter
    failed_counter = 0
    print(download_cmd)
    logging.info(download_cmd)
    
    try:
        k = subprocess.run(download_cmd, shell=True, timeout=600)  # Add timeout
        if "visionias" in cmd and k.returncode != 0 and failed_counter <= 10:
            failed_counter += 1
            await asyncio.sleep(5)
            await download_video(url, cmd, name)
        failed_counter = 0
    except subprocess.TimeoutExpired:
        print(f"Download command timed out: {download_cmd}")
        return None
    except Exception as e:
        print(f"Error running download command: {str(e)}")
        return None
        
    try:
        if os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        elif os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        elif os.path.isfile(f"{name}.mp4.webm"):
            return f"{name}.mp4.webm"

        return f"{name}.mp4"
    except Exception as exc:
        print(f"Error determining file path: {str(exc)}")
        return f"{name}.mp4"

async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name, channel_id):
    try:
        reply = await bot.send_message(channel_id, f"Downloading pdf:\n<pre><code>{name}</code></pre>")
        await asyncio.sleep(1)
        start_time = time.time()
        await bot.send_document(chat_id=channel_id, document=ka, caption=cc1)
        count += 1
        await reply.delete(True)
        await asyncio.sleep(1)
        os.remove(ka)
        await asyncio.sleep(3)
    except Exception as e:
        print(f"Error in send_doc function: {str(e)}")

def decrypt_file(file_path, key):  
    try:
        if not os.path.exists(file_path): 
            return False  

        with open(file_path, "r+b") as f:  
            num_bytes = min(28, os.path.getsize(file_path))  
            with mmap.mmap(f.fileno(), length=num_bytes, access=mmap.ACCESS_WRITE) as mmapped_file:  
                for i in range(num_bytes):  
                    mmapped_file[i] ^= ord(key[i]) if i < len(key) else i 
        return True
    except Exception as e:
        print(f"Error decrypting file {file_path}: {str(e)}")
        return False

async def download_and_decrypt_video(url, cmd, name, key):  
    try:
        video_path = await download_video(url, cmd, name)  
        
        if video_path and os.path.exists(video_path):  
            decrypted = decrypt_file(video_path, key)  
            if decrypted:  
                print(f"File {video_path} decrypted successfully.")  
                return video_path  
            else:  
                print(f"Failed to decrypt {video_path}.")  
                return video_path  # Return the original file even if decryption fails
        return video_path
    except Exception as e:
        print(f"Error in download_and_decrypt_video: {str(e)}")
        return None

async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog, channel_id):
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
            
        subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', shell=True)
        await prog.delete(True)
        reply1 = await bot.send_message(channel_id, f"**📩 Uploading Video 📩:-**\n<blockquote>**{name}**</blockquote>")
        reply = await m.reply_text(f"**Generate Thumbnail:**\n<blockquote>**{name}**</blockquote>")
        thumbnail = None
        try:
            if thumb == "/d":
                thumbnail = f"{filename}.jpg"
            else:
                thumbnail = thumb
        except Exception as e:
            await m.reply_text(str(e))
        
        # Set a default thumbnail if none was provided or generated
        if thumbnail is None or not os.path.exists(thumbnail):
            thumbnail = f"{filename}.jpg"
          
        dur = int(duration(filename))
        start_time = time.time()

        try:
            await bot.send_video(channel_id, filename, caption=cc, supports_streaming=True, height=720, width=1280, thumb=thumbnail, duration=dur, progress=progress_bar, progress_args=(reply, start_time))
        except Exception:
            await bot.send_document(channel_id, filename, caption=cc, progress=progress_bar, progress_args=(reply, start_time))
        os.remove(filename)
        await reply.delete(True)
        await reply1.delete(True)
        if os.path.exists(f"{filename}.jpg"):
            os.remove(f"{filename}.jpg")
    except Exception as e:
        print(f"Error in send_vid function: {str(e)}")
        raise