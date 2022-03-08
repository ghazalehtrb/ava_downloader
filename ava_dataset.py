# -*- coding: utf-8 -*-
import requests
import os
import subprocess
from tqdm import tqdm
import argparse


BROKEN_LIST = []

# Check class ids
def video_info(data_block, target_cls):
  index_list = list(data_block.index)
  vids_cls = {}
  for i in index_list:
    video_id = data_block.loc[i]['video_id']
    action_id = int(data_block.loc[i]['action_id'])
    if action_id in target_cls:
      vids_cls[video_id] = action_id

  return vids_cls

# For each filename in file, download

def download_file(filename, cls_id, mode='trainval', base_dir=""):
  url = 'https://s3.amazonaws.com/ava-dataset/{}/{}'.format(mode, filename)
  file_path = "{}/{}/{}".format(base_dir, cls_id, filename)
  
  if not os.path.isdir(base_dir):
      os.mkdir(base_dir)
  if not os.path.isdir(os.path.join(base_dir, str(cls_id))):
    os.mkdir(os.path.join(base_dir, str(cls_id)))
  
  if check_file(filename, base_dir):
    print("\tFile {} already exists. Skipping.".format(filename))
  else:
    print("\tDownloading file {} from url: {}".format(filename, url))
    r = requests.get(url, allow_redirects=True)
    print("\tWriting file {} to disk.".format(filename))
  try:
    open(file_path, 'wb').write(r.content)
  except:
    BROKEN_LIST.append(file_path)

def read_url_file(path):
  filenames = [line.rstrip('\n') for line in open(path)]
  return filenames

def check_file(filename, cls_id, base_dir):
  url = "{}/{}".format(base_dir, cls_id, filename)
  return os.path.isfile(url)

def process_video(filename, base_dir, output_dir):
   # Construct command to trim the videos (ffmpeg required).
    
    start_time = 900
    end_time = 1800
    input_filename = "{}/{}/{}".format(base_dir, cls_id, filename)
    output_filename = "{}/{}/{}_900_1800.mp4".format(output_dir, cls_id, filename)
    status = False

    if(not check_file(filename, base_dir)):
      print("\tFile does not exist. Skipping:")
    elif(check_file(output_filename, ".")):
      print("\tVideo already processed. Skipping:")
    else:
      command = ['ffmpeg',
                 '-i', '"%s"' % input_filename,
                 '-ss', str(start_time),
                 '-t', str(end_time - start_time),
                 '-c:v', 'libx264', '-c:a', 'ac3', #ac3 needed for some videos
                 '-threads', '1',
                 '-loglevel', 'panic',
                 '"{}"'.format(output_filename)]
      command = ' '.join(command)

      try:
          print("\tProcessing video: {}".format(filename))
          output = subprocess.check_output(command, shell=True,
                                           stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as err:
          print(status, err.output)
          return status, err.output

      # Check if the video was successfully saved.
      status = os.path.exists(output_filename)
    return status

#Parser time

parser = argparse.ArgumentParser()
parser.add_argument( "input" , help="Filename of file with video filenames")
parser.add_argument("--annot", "-a", help="annotations", default="ava_train_v2.1.csv")
parser.add_argument("--target_cls", "-t", help="id of target classes seperated by ,", default="59,36,47,78")
parser.add_argument("--video_dir", "-v", help="Directory to store downloaded videos", default="ava_dataset")
parser.add_argument("--output_dir", "-o", help="Directory to store processed videos", default="processed")
parser.add_argument("--mode", "-m", help="Whether it's trainval or test mode", default="trainval")
parser.add_argument("-f", "--function", help="Whether you want to download, cut videos or do both. Values are: 'd', 'c', 'dc'", default='d')

args = parser.parse_args()
annot_file = args.annot
input_file = args.input
target_cls = args.target_cls.split(',')

csvfile = pd.read_csv("ava_v2.1/" + annot_file , encoding= 'unicode_escape')
videos_cls = video_info(csvfile, target_cls)

base_dir = args.video_dir
output_dir = args.output_dir
mode = args.mode
function = args.function
videos = read_url_file(input_file)

# Download and/or process each video in file
for i, filename in enumerate(tqdm(videos)):
  if filename.split('.')[0] in videos_cls:
    cls_id = videos_cls[filename.split('.')[0]]
    if function.find('d')>=0:
      download_file(filename, mode, base_dir)
    if function.find('c')>=0:  
      process_video(filename,base_dir,output_dir)

print(set(BROKEN_LIST))
