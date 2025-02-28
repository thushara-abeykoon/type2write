import base64
import json
import os
import threading
from http.client import HTTPException
from traceback import print_tb

import cv2
import requests
from flask import jsonify, send_file

from font_config.font_template import FontTemplate
from font_config.glyph_manager import get_paths, glyph_creator, get_max_width
from manual_config.image_config import request_svg, get_status, enhance_image, remove_background


class FontConfig:

    def __init__(self, font_type="manual"):
        self.available_files = list(map(lambda x: chr(x), range(65, 91)))
        self.current_user_email = None
        self.files_list: list = []
        self.user_folder = None
        self.uploads_folder = None
        self.svg_folder = None
        self.rembg_folder = None
        self.convert_error = False
        self.image_status: dict = {}
        self.status = {"status": "uploading images"}
        self.font_name = None
        self.font_type = font_type

    def create_necessary_dirs(self):
        self.directory_maker("users")
        self.user_folder = self.directory_maker(os.path.join("users", self.current_user_email))
        self.user_folder = self.directory_maker(os.path.join(self.user_folder, self.font_type))
        self.uploads_folder = self.directory_maker(os.path.join(self.user_folder, 'uploads'))
        self.svg_folder = self.directory_maker(os.path.join(self.user_folder, 'svgs'))

    def get_upload(self, current_user_email, files_list, files_type):

        self.current_user_email = current_user_email
        self.files_list = files_list

        self.create_necessary_dirs()

        if files_type == "base64":
            try:
                for character in files_list:
                    name = character['name']
                    data = character['data']
                    file_format = data.split(';')[0].split('/')[1]
                    base64_data = data.split(',')[1].encode('utf-8')
                    with open(f'{os.path.join(self.uploads_folder, name)}.{file_format}', 'wb') as file:
                        file.write(base64.decodebytes(base64_data))
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 500
        else:
            for available_file in self.available_files:
                file = self.files_list[available_file]
                save_name = f"{available_file}.{file.filename.split('.')[-1]}"
                self.image_status.update({save_name.split('.')[0]: 'converting'})
                file.save(os.path.join(self.uploads_folder, save_name))

        threading.Thread(target=self.convert_images_into_svg).start()
        return jsonify({'upload_success': True}), 200

    def is_all_files_available(self):
        if len(self.files_list) == 0:
            return False
        for available_char in self.available_files:
            try:
                self.files_list[available_char]
            except Exception:
                return False

        return True

    @staticmethod
    def directory_maker(folder_path):
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        return folder_path

    def enhance_and_rembg(self):
        self.rembg_folder = self.directory_maker(os.path.join(self.user_folder, 'rembg'))
        for image_name_with_extension in os.listdir(self.uploads_folder):
            image_path = os.path.join(self.uploads_folder, image_name_with_extension)
            image_name = image_name_with_extension.split('.')[0]
            enhanced_cv2_image = enhance_image(cv2.imread(image_path))


            background_removed_image = remove_background(enhanced_cv2_image)
            background_removed_image.save(os.path.join(self.rembg_folder, f"{image_name}.png"), 'PNG')
            # cv2.imwrite(os.path.join(self.rembg_folder, f"{image_name.split('.')[0]}.png"), background_removed_image)


    def convert_images_into_svg(self):
        self.status.update({"status": "enhancing and background removing"})
        self.enhance_and_rembg()
        self.status.update({"status": "converting images into svg"})
        json_res = None
        for image_name in os.listdir(self.rembg_folder):
            image_response =  request_svg(os.path.join(self.rembg_folder, image_name), 0)
            print(image_response)

            if image_response['code'] == 200:
                convert_id = image_response['data']['id']
            else:
                convert_id = None
                self.image_status.update({image_name.split('.')[0]: "convert_error"})

            while True and convert_id is not None:
                res = get_status(convert_id)
                json_res = json.loads(res.text)

                if json_res['code'] == 200:
                    convert_status = json_res['data']['step']
                    print(convert_status)
                    if convert_status != 'convert':
                        self.image_status.update({image_name.split('.')[0]: "convert_finished"})
                        break
                else:
                    print("Error")
                    raise HTTPException(json_res['code'])

            if json_res is not None:
                image_url = json_res['data']['output']['url']
                image_response = requests.get(image_url)
                self.save_svg(image_response.content, f"{image_name.split('.')[0]}.svg")

        print(self.image_status)
        self.status.update({"status": "font making started"})

    def save_svg(self, content, filename):
        with open(os.path.join(self.svg_folder, filename), 'wb') as svg_image:
            svg_image.write(content)

    def create_font(self, font_name, font_family):
        self.font_name = font_name
        json_res = None
        font_template = FontTemplate(font_name=font_name, font_family=font_family, font_style="regular",
                                     font_weight="600")

        glyph_list = []

        for svg_image in os.listdir(self.svg_folder):
            unicode_name = svg_image.split('.')[0]
            paths = get_paths(os.path.join(self.svg_folder, svg_image))
            if paths:
                max_width = max(list(map(lambda x: get_max_width(x), paths)))

                glyph = glyph_creator(glyph_name=unicode_name, unicode=unicode_name, data=paths,
                                      horizontal_space=max_width)

                glyph_list.append(glyph)

        font_template.create_font(glyph_list)

        with open(os.path.join(self.user_folder, 'font.svg'), 'wb') as svg_file:
            svg_file.write(font_template.get_svg_font().encode('utf-8'))

        self.status.update({"status": "svg font making finished"})

        response = font_template.request_ttf(0)

        if response['code'] == 200:
            convert_id = response['data']['id']
            self.status.update({"status": "svg font to ttf conversion started"})
        else:
            convert_id = None
            self.status.update({"status": "svg font to ttf conversion failed"})

        while True and convert_id is not None:
            res = get_status(convert_id)
            json_res = json.loads(res.text)

            if json_res['code'] == 200:
                convert_status = json_res['data']['step']
                print(convert_status)
                if convert_status != 'convert':
                    self.status.update({"status": "converting svg to ttf"})
                    break
            else:
                print("Error")
                raise HTTPException(json_res['code'])

        if json_res is not None:
            font_url = json_res['data']['output']['url']
            font_file = requests.get(font_url)

            with open(os.path.join(self.user_folder, f'{self.font_name}.ttf'), 'wb') as ttf_file:
                ttf_file.write(font_file.content)

            self.status.update({"status": "font making completed"})

    def get_font(self):
        font_path = f"{self.user_folder}/{self.font_name}.ttf"
        if self.font_name is None or os.path.exists(font_path):
            return {"error": "font is not created yet"}, 402
        return send_file(path_or_file=font_path), 200
