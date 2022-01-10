import PySimpleGUI as sg
import requests_html
from googletrans import Translator
import random
import time
import datetime
from threading import Thread
from collections import defaultdict
import csv
import os
import queue
job_queue = queue.Queue()
sg.theme('DarkGrey13')


class Trans:
    def __init__(self):
        self.tr = Translator(service_urls=['translate.googleapis.com'])
        self.sleeptime = datetime.timedelta(seconds=15)
        self.bef_time = datetime.datetime.now()

    def trans(self, ptext):
        """15秒ごとに、和文を英文に翻訳してstr型で返す

        Args:
            ptext ([type]): [description]

        Returns:
            [type]: [description]
        """
        while datetime.datetime.now() - self.bef_time <= self.sleeptime:
            time.sleep(1)

        print(ptext)
        while True:
            try:
                text = self.translator.translate(ptext, dest='en', src='ja')
                break
            except Exception as e:
                self.translator = Translator(service_urls=['translate.googleapis.com'])
                print('err')
        self.bef_time = datetime.datetime.now()
        return text.text


def get_nobel(base_url, cnt):
    """
    指定したurlの、cnt番目の小説本文を取得する
    取得した小説本文は、改行で区切ったリストとして返す
    """
    # base_url = 'https://ncode.syosetu.com/n6475db/'

    # cnt = 532
    url = base_url + str(cnt) + '/'
    session = requests_html.HTMLSession()
    r = session.get(url)
    # texts = r.html.full_text
    id = 'novel_honbun'
    nobel = r.html.find('#' + id, first=True)
    if nobel is None:
        return None
    return nobel.text.split('\n')


def randTranslator(pjatext_list, rate):
    # text_listのランダムな要素を英訳したものを返す
    # 翻訳する割合はrate
    text_list = pjatext_list[:]  # イミュータブルのリストは浅いコピー
    tr = Trans()

    # print(text_list)
    for i, text in enumerate(text_list):
        if len(text) >= 3 and random.random() <= rate:
            trans_text = tr.trans(text)
            text_list[i] = trans_text

    print('end_randTranslator')
    return text_list


def get_data(base_url, cnt):
    """base_urlのcnt番目の小説を取得し、英訳する
    結果は、get_data.text_ofに格納する
    Args:
        base_url ([type]): [description]
        cnt ([type]): [description]
    """
    if base_url[-1] != '/':
        base_url += '/'
    if get_data.text_of[base_url + cnt] != 0:
        return get_data.text_of[base_url + cnt]

    jatext_list = get_nobel(base_url, cnt)
    jatext = '\n'.join(jatext_list)
    if jatext_list:  # 小説が取得できた場合だけ処理する
        entext_list = randTranslator(jatext_list, 0.1)
        entext = '\n'.join(entext_list)
        get_data.text_of[base_url + cnt] = (entext, jatext)
        write_nobel_csv(base_url, cnt, entext, jatext)
        return True
    else:  # 取得できない場合はFalseを返す
        return False


# urlに対して、既に取得したデータ
get_data.text_of = defaultdict(int)


def startup():
    # csvから今まで取得したデータを持ってくる
    save_dir = get_save_dir()
    csv_name = 'NEL_data.csv'
    csv_path = os.path.join(save_dir, csv_name)
    if not os.path.exists(save_dir):
        # create save_dir
        print('create save_dir')
        print(save_dir)
        os.mkdir(save_dir)
        return
    if not os.path.exists(csv_path):
        return
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                print(row[0])
                get_data.text_of[row[0]] = (row[1], row[2])


def write_nobel_csv(base_url, cnt, entext, jatext):
    save_dir = get_save_dir()
    csv_name = 'NEL_data.csv'
    csv_path = os.path.join(save_dir, csv_name)
    # cp932のエラーを回避する
    b = entext.encode('cp932', "ignore")
    entext = b.decode('cp932')
    b = jatext.encode('cp932', "ignore")
    jatext = b.decode('cp932')

    # csvに書き込む
    with open(csv_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([base_url + str(cnt), entext, jatext])


def write_last_session(base_url, cnt):
    # 最後に実行した状態を記録する
    save_dir = get_save_dir()
    csv_name = 'last_session.csv'
    csv_path = os.path.join(save_dir, csv_name)
    with open(csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([base_url, cnt])


def get_save_dir():
    app_dir = os.environ.get("APPDATA")
    this_dir = 'NEL_data'
    save_dir = os.path.join(app_dir, this_dir)
    return save_dir


def read_last_session():
    # 最後に実行した状態を読み込む
    # py_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = get_save_dir()
    csv_name = 'last_session.csv'
    csv_path = os.path.join(save_dir, csv_name)
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                return row


def get_data_thread():
    while True:
        while job_queue.qsize() > 0:
            base_url, cnt = job_queue.get()
            if get_data.text_of[base_url + str(cnt)] == 0:
                get_data(base_url, cnt)
        time.sleep(1)


def downloadall(base_url):
    print('downloadall_start')
    cnt_i = 1
    while True:
        print(base_url, cnt_i)
        is_available = get_data(base_url, str(cnt_i))
        if not is_available:
            return
        cnt_i += 1


def main():
    # sg.theme('Default')   # デザインテーマの設定
    startup()
    is_en = True
    # ウィンドウに配置するコンポーネント
    layout = [[sg.Text('対象の小説url'), sg.InputText('url', size=50, key='base_url'), sg.Text('EN', key='en_or_ja')],
            [sg.Text('対象の小説和数'), sg.InputText(999, size=5, key='cnt'), sg.Text('データの保存先'), sg.Text(get_save_dir())],
            [sg.Multiline(size=(40, 20), key='text', font=(None, 20)), sg.Multiline(size=(40, 20), key='jatext', font=(None, 20), visible = False)],
            [sg.Button('Run', bind_return_key=True), sg.Button('Next'), sg.Button('Prev'), sg.Button('Update'), sg.Button('Ja<->En'), sg.Button('DownLoadAll')]]

    # ウィンドウの生成
    window = sg.Window('Narou', layout, margins=(0,0), resizable=True, finalize=True)
    window["text"].expand(expand_x=True, expand_y=True)  # サイズを可変に

    # データ取得スレッドを起動
    Thread(target=get_data_thread, args=(), daemon=True).start()

    def run(base_url, cnt, is_en):
        text = get_data.text_of[base_url + cnt]
        if text == 0:
            text = ('Please Run and Wait', 'Please Run and Wait')
        # set output
        values['text'] = text[0]
        values['jatext'] = text[1]
        window.Element('text').update(values['text'])
        window.Element('jatext').update(values['jatext'])

    # 前回実行時の情報を取得

    event, values = window.read()
    last_session = read_last_session()

    if last_session:
        base_url, cnt = last_session
        values['base_url'] = base_url
        values['cnt'] = cnt
        window.Element('cnt').update(values['cnt'])
        window.Element('base_url').update(values['base_url'])
        run(base_url, cnt, is_en)

    # イベントループ
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Run':
            # get_input
            base_url = values['base_url']
            cnt = values['cnt']
            run(base_url, cnt, is_en)
            # 小説の取得処理は、別スレッドで行う
            job_queue.put((base_url, cnt))
            job_queue.put((base_url, str(int(cnt)+1)))
            job_queue.put((base_url, str(int(cnt)-1)))
        elif event == 'Next':
            cnt = values['cnt']
            cnt = str(int(cnt)+1)
            values['cnt'] = cnt
            run(base_url, cnt, is_en)
            window.Element('cnt').update(values['cnt'])
            for i in range(10):
                job_queue.put((base_url, str(int(cnt)+i)))
        elif event == 'Prev':
            cnt = values['cnt']
            cnt = str(int(cnt)-1)
            values['cnt'] = cnt
            run(base_url, cnt, is_en)
            window.Element('cnt').update(values['cnt'])
            for i in range(10):
                job_queue.put((base_url, str(int(cnt)-i)))
            # window.read()
        elif event == 'Update':
            base_url = values['base_url']
            cnt = values['cnt']
            run(base_url, cnt, is_en)
        elif event == 'Ja<->En':
            is_en = not is_en
            base_url = values['base_url']
            cnt = values['cnt']
            window['jatext'].update(visible=(not is_en))
            window['text'].update(visible=is_en)
            if is_en:
                window["text"].expand(expand_x=True, expand_y=True)
            else:
                window["jatext"].expand(expand_x=True, expand_y=True)
            window['en_or_ja'].update('EN' if is_en else 'JA')
        elif event == 'DownLoadAll':
            base_url = values['base_url']
            Thread(target=downloadall, args=(base_url,), daemon=True).start()

    window.close()
    write_last_session(base_url, cnt)
    print('end')


main()
