import csv
import re
import subprocess
from pathlib import Path
import math
from time import sleep
import flet
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    Row,
    Column,
    Text,
    TextButton,
    TextField,
    Checkbox,
    ProgressBar,
    icons,
)

moviePath = ""
csvPath = ""

def main(page: Page):

    # MOV指定用のダイアログ
    def mov_file_result(e: FilePickerResultEvent):
        global moviePath
        movie_file.value = (
            ", ".join(map(lambda f: f.name, e.files)
                      ) if e.files else "Cancelled!"
        )
        if movie_file.value == "Cancelled!":
            moviePath = "Cancelled!"
        else:
            moviePath = str(e.files[0].path)

        movie_file.update()

    movie_file_dialog = FilePicker(on_result=mov_file_result)
    movie_file = Text()

        # CSV指定用のダイアログ
    def csv_file_result(e: FilePickerResultEvent):
        global csvPath
        csv_file.value = (
            ", ".join(map(lambda f: f.name, e.files)
                      ) if e.files else "Cancelled!"
        )
        if csv_file.value == "Cancelled!":
            csvPath = "Cancelled!"
        else:
            csvPath = str(e.files[0].path)

        csv_file.update()

    csv_file_dialog = FilePicker(on_result=csv_file_result)
    csv_file = Text()

        # 保存先指定用ダイアログ
    def get_savedirectory_result(e: FilePickerResultEvent):
        savedirectory_path.value = e.path if e.path else "Cancelled!"
        savedirectory_path.update()

    get_savedirectory_dialog = FilePicker(on_result=get_savedirectory_result)
    savedirectory_path = Text()

    def load_csv(csv_path):
        filename = csv_path
        with open(filename, encoding='shift_jis', newline='') as f:
            csv_reader = csv.reader(f)
            content = [row for row in csv_reader]
        return content

    def text_changed(e):
        testsinbol.value = sbname.value + "_[cut].[ext]"
        page.update()

    def checkbox_changed(e):
        output_text.value = str(audio_check.value)
        page.update()

    def ok_click(e):
        if movie_file != None and movie_file != "Cancelled!":
            is_csv = csvPath.endswith(".csv")
            is_movie = moviePath.endswith(".mov") or moviePath.endswith(".mp4")

            if is_csv and is_movie:
                split_movie(moviePath, load_csv(csvPath), savedirectory_path.value, audio_check.value)

    def split_movie(movie, csv, save_folder, audio=True):
        total_items = len(csv)
        total_value = total_items+1
        
        # Use ProgressBar to show progress
        pb = ProgressBar(value=0,width=400)
        pro = Column([Text("Processing..."), pb])
        
        page.add(
            pro
            )
        
        for index, item in enumerate(csv):
            stt, edt = float(item[1]), float(item[2])
            all_frame = int(edt - stt)
            frame_rate, width, height = get_frame_rate_and_size(movie)

            stt_secs = stt / frame_rate
            edt_secs = edt / frame_rate
            
            time_text = convert_frames_to_time(all_frame,frame_rate)
            print(time_text)
            trim_name = f"{save_folder}\\{item[0].split('.')[0]}.mov"
            render_name = f"{save_folder}\\{sbname.value}_{item[0].split('.')[0]}.mov"
            clip_name = sbname.value+"_"+item[0].split('.')[0]
            bold_duration = int(bold.value)
            trim_command, bold_command, delete_command = build_command(movie, stt_secs, edt_secs, trim_name, render_name, clip_name, time_text, width, audio,bold_duration,frame_rate)

            if(bold_duration==0):
                subprocess.run(r"ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" + trim_command, shell=True)
            else:
                subprocess.run(r"ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" + trim_command, shell=True)
                subprocess.run(r"ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" + bold_command, shell=True)
                subprocess.run(delete_command, shell=True)

            pb.value = index / total_value
            page.update()
        pb.value = 1.0
        page.remove(pro)
           
    def get_frame_rate_and_size(movie_path):
        command = [r"ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe", '-i', movie_path]
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        match_rate = re.search(r'(\d+\.?\d*) fps', result.stderr)
        match_size = re.search(r"Stream #\d+:\d+(.+), (\d+)x(\d+)", result.stderr)
        rate = float(match_rate.group(1))
        
        if(rate == 23.98):
            frame_rate = 24000 / 1001
        else:
            frame_rate = rate

        width, height = int(match_size.group(2)), int(match_size.group(3))
        return frame_rate, width, height

    def convert_frames_to_time(frame_count, frame_rate):
        minutes, seconds = divmod(frame_count, frame_rate * 60)
        seconds, frames = divmod(seconds, frame_rate)
        return f"{str(math.floor(minutes)).zfill(2)}\\:{str(math.floor(seconds)).zfill(2)}\\:{str(math.floor(frames)).zfill(2)}"

    def build_command(movie, stt_secs, edt_secs, trim_name, render_name, clip_name, time_text, width, audio,bold_duration,frame_rate):
               
        bold_time = bold_duration/frame_rate
        audtime = str(int(bold_time*1000))+"|"+str(int(bold_time*1000))+"|"+str(int(bold_time*1000))
        trim_command = f" -ss {stt_secs} -t {edt_secs - stt_secs} -i \"{movie}\" -c:v libx264 -crf 0 -y \"{trim_name}\""
            
        if audio:
            bold_command = (
                f" -i \"{trim_name}\" "
                f"-filter_complex \"[0:v]tpad=start_duration=0.332:color=black[v];"
                f"[v]drawtext=text='{clip_name}':fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:font=meiryo:fontsize={int(width/20)}:enable='between(t,0,0.332)'[v1];"
                f"[v1]drawtext=text='{time_text}':fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+{int(width/20)}:font=meiryo:fontsize={int(width/20)}:enable='between(t,0,0.332)'[v2];"
                f"[0:a]adelay='{audtime}'[a]\" "
                f"-map \"[v2]\" -map \"[a]\" -c:v libx264 -c:a aac -crf 0 -y \"{render_name}\""
            )
        else:
            bold_command = (
                f" -i \"{trim_name}\" "
                f"-filter_complex \"[0]tpad=start_duration=0.332:color=black[v];"
                f"[v]drawtext=text='{clip_name}':fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:font=meiryo:fontsize={int(width/20)}:enable='between(t,0,0.332)'[v1];"
                f"[v1]drawtext=text='{time_text}':fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+{int(width/20)}:font=meiryo:fontsize={int(width/20)}:enable='between(t,0,0.332)'[v2]\" "
                f"-map \"[v2]\" -c:v libx264 -crf 0 -y \"{render_name}\""
            )

        delete_command = f"del \"{trim_name}\""

        return trim_command, bold_command, delete_command

    audio_check = Checkbox(label="Contains audio : ", value=True, on_change=checkbox_changed)
    output_text = Text("True")
    sbname = TextField(label="symbol name : AA_AA", on_change=text_changed)
    testsinbol = Text("---_---_---")
    bold = TextField(label="bold",value="8")
    movie_file_dialog = FilePicker(on_result=mov_file_result)
    movie_file = Text()

    csv_file_dialog = FilePicker(on_result=csv_file_result)
    csv_file = Text()

    get_savedirectory_dialog = FilePicker(on_result=get_savedirectory_result)
    savedirectory_path = Text()

    progress_bar = ProgressBar()
    
    page.title = "Cut Splitter"
    page.window_height, page.window_width = 490, 650
    page.overlay.extend([movie_file_dialog, csv_file_dialog, get_savedirectory_dialog])

    page.add(
        Row(
            [
                ElevatedButton(
                    "MOVIE file",
                    icon=icons.UPLOAD_FILE,
                    on_click=lambda _: movie_file_dialog.pick_files(allow_multiple=False),
                ),
                movie_file,
            ]
        ),
        Row(
            [
                ElevatedButton(
                    "CSV file",
                    icon=icons.UPLOAD_FILE,
                    on_click=lambda _: csv_file_dialog.pick_files(allow_multiple=False),
                ),
                csv_file,
            ]
        ),
        Row(
            [
                ElevatedButton(
                    "Open directory",
                    icon=icons.FOLDER_OPEN,
                    on_click=lambda _: get_savedirectory_dialog.get_directory_path(),
                ),
                savedirectory_path,
            ]
        ),
        Row([bold]),
        Row([sbname]),
        Row([testsinbol]),
        Row([audio_check, output_text]),
        Row([TextButton("tear into shreds", on_click=ok_click)]),
    )

flet.app(target=main)


