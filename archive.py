#!/usr/bin/env python3

import yt_dlp as youtube_dl
import sys
import time
import logging
import json
import os
from datetime import datetime
import subprocess
import click
import atexit
import requests

from yt_dlp.utils import DownloadError, DateRange, match_filter_func

format = 'bestvideo[height>1080]+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
metadata = {'key': 'FFmpegMetadata'}
subtitles = {'key': 'FFmpegEmbedSubtitle'}
thumbnail = {'key': 'EmbedThumbnail','already_have_thumbnail': False}

notif_url = "https://api.pushover.net/1/messages.json"
notif_token_var = 'PUSHOVER_TOKEN'
notif_user_var = 'PUSHOVER_USER'

def send_notif(msg):
	if notif_token_var in os.environ and notif_user_var in os.environ:
		notif_token = os.environ[notif_token_var]
		notif_user = os.environ[notif_user_var]

		requests.post(notif_url, data = {
			"token": notif_token,
			"user": notif_user,
			"message": msg,
			"priority": -1,
		})

class Logger(object):
	def cycle_logs(log_path):
		for i in range(5,0,-1):
			log = os.path.join(os.getcwd(),log_path+"."+str(i-1))
			if not os.path.isfile(log):
				continue
			os.rename(log,os.path.join(os.getcwd(),log_path+"."+str(i)))

		log = os.path.join(os.getcwd(),log_path)
		if os.path.isfile(log):
			os.rename(log,os.path.join(os.getcwd(),log_path+".0"))

	def __init__(self, log_path):
		logging.basicConfig(filename=log_path, level=logging.INFO)

	def debug(self, msg):
		logging.info(msg)

	def warning(self, msg):
		logging.warning(msg)

	def error(self, msg):
		logging.error(msg)
		if not ('supported for thumbnail embedding' in msg or 'Premieres' in msg):
			notif_msg = "Error occurred updating YouTube archive: " + msg
			send_notif(notif_msg)

@click.command()
@click.option('-f', '--file', type=click.File('r'),
				help='A file containing URLs or video IDs to download.')

@click.option('-o', '--outdir', 'download_dir',
				type=click.Path(file_okay=False, writable=True),
				default='downloads', show_default=True,
				help='The directory to download videos into.')

@click.option('-k', '--keep', default=False, is_flag=True,
				help='Keep downloaded files in the download directory.')

@click.option('-a', '--archive', 'archive_dir',
				type=click.Path(file_okay=False, writable=True),
				default='Archives', show_default=True,
				help='The directory to move finished files into. Ignored if \'-k\' is passed')
@click.option('--log-path', type=click.Path(dir_okay=False, writable=True),
				default='archive.log', show_default=True,
				help='The file to log to.')

@click.option('--options', type=str,
				help='Any options to pass to yt-dlp for all downloads. Should be\
formatted as a python dictionary.')

@click.option('-n', '--notifications', 'notifications', is_flag=True,
				help='Send notifications for the start of each video download. \
Without this, notifications will still be sent upon completion.')

@click.option('-c', '--count', 'download_count', type=int,
				help='Limit the number of videos downloaded.')

@click.option('--use-cookies', 'use_cookies', type=str,
				help='The name of the browser to load cookies from.')

@click.argument('urls', nargs=-1, type=str)
def main(file,
			download_dir,
			keep,
			archive_dir,
			log_path,
			options,
			notifications,
			download_count,
			use_cookies,
			urls):

	global lock_path
	lock_path = os.path.join(download_dir,'.lock')

	if not os.path.isdir(download_dir):
		os.mkdir(download_dir)

	if os.path.isfile(lock_path):
		print('waiting for lock on download directory...')
		retry_count = 0
		while os.path.isfile(lock_path):
			time.sleep(60)
			retry_count += 1
			if retry_count == 10:
				send_notif("Archive updater has been blocked for 10 minutes")
			elif retry_count > 30:
				exit(1)

	open(lock_path,'w').close()

	if log_path == 'archive.log':
		Logger.cycle_logs(log_path)

	def cleanup():
		os.remove(lock_path)

	atexit.register(cleanup)

	if file:
		entries = file.read().splitlines()
	else:
		entries = []

	for url in urls:
		entries.append(url)


	start = time.time()

	logger = Logger(log_path)

	args = {
	   'format':format,
	   'outtmpl':download_dir+'/%(title)s [%(uploader)s] (%(upload_date)s).%(ext)s',
 	   'download_archive':'download archive.txt',
	   'writethumbnail':True,
	   'postprocessors':[metadata, subtitles, thumbnail],
	   'logger':logger,
	   'noprogress':True,
	   'ignoreerrors':True,
	   'writesubtitles':True,
	   'subtitleslangs':['all','-live_chat'],
	   'retries':10,
	   'fragment_retries':10,
	   'allow_playlist_files':False,
	   'cookiesfrombrowser': (use_cookies,) if use_cookies else None
	}

	if options:
		args = args | json.loads(options)

	ydl = youtube_dl.YoutubeDL(args)

	base_params = ydl.params

	global downloaded_videos
	downloaded_videos = []

	for entry in entries:
		if entry.lstrip().startswith("#"):
			continue

		if not ';' in entry:
			entry = entry + ';0'

		url,opts = entry.split(';')
		opts = opts.split('::')

		count = int(opts[0])
		if download_count != None:
			ydl.params['playlistend'] = download_count
		elif count > 0:
			ydl.params['playlistend'] = count

		if len(opts) == 2:
			extra_params = json.loads(opts[1])

			if 'match_filter' in extra_params:
				extra_params['match_filter'] = match_filter_func(extra_params['match_filter'])

			if 'dateafter' in extra_params:
				extra_params['daterange'] = DateRange(extra_params['dateafter'])
				del extra_params['dateafter']

			ydl.params = base_params | extra_params

		global video_title
		video_title = ''

		def callback(progress):
			global video_title
			global dl_count

			status = progress['status']
			if status == 'downloading' and 'title' in progress['info_dict']:
				new_title = progress['info_dict']['title']
				if notifications and new_title != video_title:
					send_notif("Now downloading: " + new_title)
				video_title = new_title

			if status == 'finished' and 'title' in progress['info_dict']:
				info_dict = progress['info_dict']
				video_info = (info_dict['title'], info_dict['uploader'])
				if not downloaded_videos or downloaded_videos[-1] != video_info:
					downloaded_videos.append(video_info)

		attempts = 0
		code = -1

		ydl.add_progress_hook(callback)

		while attempts < 5:
			code = ydl.download([url])
			if code == 0:
				break
			time.sleep(10)
			attempts+=1

		if code != 0:
			send_notif("Failed to download '{}', code {}".format(video_title, code))

		ydl.params = base_params
		ydl._progress_hooks = []
		ydl._download_retcode = 0

	dl_count = len(downloaded_videos)

	for file in os.listdir(download_dir):
		if file == '.lock' or file == '.DS_Store':
			continue
		fname,ext = os.path.splitext(file)

		if fname.endswith(")"):
			date = fname.rpartition("(")[2].rstrip(")")
			datestr = datetime.strptime(date,"%Y%m%d").strftime("\"%m/%d/%Y 10:00\"")
			cmd = "SetFile -md " + datestr + " $'" + os.path.join(download_dir,file).replace("'","\\'") + "'"
			result = subprocess.call(cmd, shell=True)
			if result != 0:
				exit(result)

		if not keep:
			if not os.path.isdir(archive_dir):
				os.mkdir(archive_dir)
			os.rename(os.path.join(download_dir,file),os.path.join(archive_dir, file))


	runtime = time.time() - start
	logger.debug("downloaded " + str(dl_count) + " videos in " + str(runtime) + " seconds")
	if dl_count == 0:
		notif_msg = "Archive updated, no new videos added."
	elif dl_count == 1:
		(title, uploader) = downloaded_videos[0]
		notif_msg = "{} by {} added to the archive!".format(title,uploader)
	else:
		notif_msg = "{} videos added to the archive: ".format(dl_count)
		for (title, uploader) in downloaded_videos:
			notif_msg += "\n{} by {}".format(title, uploader)

	send_notif(notif_msg)
	
	atexit.unregister(cleanup)
	cleanup()
	if not keep:
		try:
			os.rmdir(download_dir)
		except:
			pass

if __name__ == '__main__':
	main()
