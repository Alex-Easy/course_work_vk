import requests
import os
import json
import tqdm
from config import TOKEN_VK, USER_ID_VK, TOKEN_YA


def create_json():
    json_data = []
    with open('log.json', 'w') as file:
        json.dump(json_data, file, indent=2, ensure_ascii=True)


create_json()


def add_to_json(param_1, param_2):
    json_data = {
        param_1: param_2
    }
    with open("log.json", "r") as file:
        data = json.load(file)
    data.append(json_data)
    with open("log.json", "w") as file:
        json.dump(data, file, indent=2, ensure_ascii=True)


class VK:
    VK_API_URL = 'https://api.vk.com/method'

    def __init__(self, token_vk, user_id_vk):
        self.token_vk = token_vk
        self.user_id = user_id_vk

    def get_common_params_vk(self):
        return {
            'access_token': self.token_vk,
            'v': '5.131'
        }

    def get_profile_photos(self):
        if not os.path.exists('backup photos VK'):
            os.mkdir('backup photos VK')
            add_to_json('backup photos VK', 'a folder has been created on the local disk')
        max_size_photo = {}
        params = self.get_common_params_vk()
        params.update({'owner_id': self.user_id, 'album_id': 'profile', 'extended': '1'})
        response = requests.get(f'{self.VK_API_URL}/photos.get', params=params)
        photos_count = 0
        for photo in response.json()['response']['items']:
            if photos_count >= 5:
                break
            max_size = 0
            photo_url = ''
            for size in photo['sizes']:
                if size['height'] >= max_size:
                    max_size = size['height']
                    photo_url = size['url']

            photo_name = f"{photo['likes']['count']}_{photo['date']}"
            with open(f'backup photos VK/{photo_name}.jpg', 'wb') as file:
                img = requests.get(photo_url)
                file.write(img.content)
                add_to_json(photo_name, 'downloaded to local disk')
            photos_count += 1


class YANDEX:
    YANDEX_API_URL = 'https://cloud-api.yandex.net'

    def __init__(self, token_ya):
        self.token_ya = token_ya

    def folder_creation(self):
        url = self.YANDEX_API_URL + '/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Authorization': self.token_ya}
        params = {'path': 'backup photos VK'}
        response = requests.put(url=url, headers=headers, params=params)
        add_to_json('backup photos VK', 'a folder has been created on Yandex Disk')

    def upload(self, file_path: str):
        url = self.YANDEX_API_URL + '/v1/disk/resources/upload'
        headers = {'Content-Type': 'application/json', 'Authorization': self.token_ya}
        file_name = os.path.basename(file_path)
        params = {'path': f'backup photos VK/{file_name}',
                  'overwrite': 'true'}

        response = requests.get(url=url, headers=headers, params=params)
        href = response.json().get('href')

        with open(file_path, 'rb') as file:
            file_size = os.path.getsize(file_path)
            uploader = requests.put(href, data=file, stream=True)
            with tqdm.tqdm(total=file_size, desc=file_name, unit='B', unit_scale=True, unit_divisor=1024) as progress_bar:
                for data_chunk in uploader.iter_content(1024):
                    progress_bar.update(len(data_chunk))


if __name__ == '__main__':
    vk_client = VK(TOKEN_VK, USER_ID_VK)
    vk_client.get_profile_photos()

    ya_client = YANDEX(TOKEN_YA)
    ya_client.folder_creation()

    photos_list = os.listdir('backup photos VK')[:5]
    for photo in photos_list:
        file_path = os.path.join(os.getcwd(), 'backup photos VK', photo)
        ya_client.upload(file_path)
        add_to_json(photo, 'uploaded to Yandex Disk')
