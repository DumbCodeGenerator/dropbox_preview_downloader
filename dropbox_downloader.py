import requests
import validators
import re
import json
import shutil
import os
import traceback
import subprocess
import string
import sys


def stop():
    input('Stopped. Press any button to continue...')
    sys.exit()


def getMore(data, session):
    more_data = []
    try:
        has_more = re.search(
            r'\\"has_more_entries\\":\s*(.*?),', data).group(1).lower() == 'true'
        next_voucher = re.search(r'\\"next_request_voucher\\":\s*\\"(.*?)\\"}"',
                                 data).group(1).replace('\\\\\\"', '"').replace('\\\\\\\\"', '\\"')
        while has_more:
            json.loads(next_voucher)
            link_key = re.search(r'"linkKey":\s*"(.*?)",', data).group(1)
            link_type = re.search(r'"linkType":\s*"(.*?)",', data).group(1)
            secure_hash = re.search(r'"secureHash":\s*"(.*?)"', data).group(1)
            t_param = session.cookies.get_dict().get('t')

            next_data = session.post('https://www.dropbox.com/list_shared_link_folder_entries', data={'is_xhr': 'true', 't': t_param, 'link_key': link_key,
                                                                                                      'link_type': link_type, 'secure_hash': secure_hash, 'voucher': next_voucher, 'sub_path': ''})

            next_data = json.loads(next_data.text)
            has_more = next_data.get('has_more_entries')
            next_voucher = next_data.get('next_request_voucher')
            next_data = next_data.get('entries')
            more_data.extend(next_data)
        return more_data
    except Exception:
        return more_data


def main():
    dropboxUrl = input('Insert dropbox url: ')

    if not re.match(r'https?:\/\/', dropboxUrl):
        dropboxUrl = 'https://' + dropboxUrl

    if not validators.url(dropboxUrl):
        print("Invalid URL")
        stop()

    do_download = input(
        'Download this images/videos? [y/n]: ').lower().startswith('y')
    session = requests.Session()

    print('Getting data from link...')
    data = session.get(dropboxUrl).text

    print('Getting all files...')
    more_data = getMore(data, session)

    folder_name = re.search(
        r'"displayName":\s*"(.*?)",\s*"ownerName":', data).group(1)
    folder_name = string.capwords(
        bytes(folder_name, 'ascii').decode('unicode-escape'))
    title = folder_name

    try:
        data = re.search(r'\\"entries\\":\s(.*?),\s\\"has_more_entries\\"',
                         data).group(1).replace('\\"', '"')
        data = json.loads(data)
    except Exception:
        data = re.search(r'"file":\s*(.*?), "fileViewerProps"', data).group(1)
        data = json.loads('[' + data + ']')
        folder_name = '.'

    if not os.path.exists(folder_name) and do_download:
        os.mkdir(folder_name)

    if len(more_data) > 0:
        data.extend(more_data)

    total = len(data)
    current = 1
    if not do_download:
        links_file = open(folder_name + '.txt', 'w')

    for entry in data:
        print(f'Downloading "{title}": {current}/{total}', end='\r')
        current += 1
        is_image = entry.get('preview').get('content').get('.tag') == 'image'
        src = entry.get('preview').get('content').get('full_size_src') if is_image else entry.get(
            'preview').get('content').get('transcode_url')
        filename = entry.get('filename')
        if do_download:
            if os.path.exists(folder_name + '/' + filename):
                continue

            try:
                if is_image:
                    with requests.get(src, stream=True) as image:
                        with open(folder_name + '/' + filename, 'wb') as file:
                            shutil.copyfileobj(image.raw, file)
                else:
                    p = subprocess.run(
                        ['ffmpeg', '-y', '-i', src, '-c', 'copy', folder_name + '/' + filename], capture_output=True)
                    if p.returncode != 0:
                        print(
                            f'Couldn\'t download video "{filename}". Maybe you have not "ffmpeg" in the PATH variable or "ffmpeg.exe" next to this script.\n')
            except:
                continue

        else:
            links_file.write(f'{src}\n')

    if not do_download:
        links_file.close()
        print(f'List of links created for "{title}"({total} links)!\n')
    else:
        print(f'"{title}" downloaded!\n')


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as err:
            print('Couldn\'t download link. Traceback:\n')
            traceback.print_exc()
            print()
            continue
