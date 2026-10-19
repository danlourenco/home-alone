#!/usr/bin/env python3
"""Prepare the user's local clip for the CRT; original/media stay gitignored.
Inspected source: 480x360, picture rows49..308; end-text cards begin ~80.6s.
Crop central344x258 (true4:3) inside the picture; retain footage through79.9465s.
Writes a review copy only. Stop/reload the TV player before installing it as tv.mp4.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('/tmp/ha-tv-edited.mp4'));a=ap.parse_args()
media=ROOT/'unity/HomeAlone/Assets/StreamingAssets/LocalMedia/tv.mp4'
original=ROOT/'sfm-work/media/tv.original.mp4';original.parent.mkdir(parents=True,exist_ok=True)
if not original.exists():shutil.copy2(media,original)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(original),'-t','79.946533',
 '-vf','crop=344:258:68:50,setsar=1','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',
 '-c:a','aac','-b:a','128k','-movflags','+faststart',str(a.output)],check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height,display_aspect_ratio','-of','json',str(a.output)]))
v=next(s for s in info['streams'] if s['codec_type']=='video')
assert v['width']*3==v['height']*4 and float(info['format']['duration'])<80.3,info
meta={'original':str(original.relative_to(ROOT)),'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
 'crop':[344,258,68,50],'end_seconds':79.946533,'output':str(a.output),'probe':info}
(original.parent/'tv-edit.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(info));print('Original preserved:',original)
