import os, sys, time, subprocess, datetime, shutil
import pydirectinput, pyautogui, pygetwindow as gw
from ruamel.yaml import YAML
import Levenshtein
import pytesseract
import json
import re
import traceback

class ConfigManager:
    def __init__(self):
        self.cfg_path = self.get_exe_path("config.yaml")
        print(f"📂 使用的設定檔: {self.cfg_path}")

        # 初始化 YAML 解析
        self.rua_yaml = YAML()
        self.rua_yaml.preserve_quotes = True   # 保留引號
        self.rua_yaml.indent(sequence=4, offset=2)

        # 載入設定
        with open(self.cfg_path, "r", encoding="utf-8") as f:
            self.config = self.rua_yaml.load(f)

        # 初始化各項路徑與配置
        self.SL_FILE = self.config.get("sl_file", "")
        self.AUTO_SELL = self.config.get("auto_sell", "")
        self.CLEAR_FILE = self.config.get("clear_file", "")

        self.MOD_TYPE = self.config["mod_type"]
        self.MOD_MANY = self.config["mod_many"]
        self.PEEK = self.config["peek"]

        self.GAME_PATH = self.config["game_path"]
        self.SOURCE_FILE = self.config["source_file"]
        self.SOURCE_FILE_BAK = self.config["source_file_bak"]

        self.OCR_PATH = self.config["ocr_path"]

        self.REGION = self.config['region']

        self.ORI_FOLDER = self.resource_path(self.config["ori_folder"])
        self.SAVE_FOLDER = self.resource_path(self.config["save_folder"])
        self.SCREENSHOT_FOLDER = self.resource_path(self.config["screenshot_folder"])
        self.ASSETS_FOLDER = self.resource_path(self.config["asset_folder"])
        self.RELIC_DIC = self.resource_path(self.config["relic_dic"])
        self.RELIC_DIC_CH = self.resource_path(self.config["relic_dic_ch"])
        self.RELIC_LOG = self.get_exe_path("relic_log.json")
        self.LOG = self.resource_path(self.config["relic_log"])
        self.WISH_POOL = self.get_exe_path(self.config["wish_pool"])
        self.IMAGES = {k: os.path.join(self.ASSETS_FOLDER, v) for k, v in self.config["images"].items()}
        
        # 載入 RElic Dic 中文
        with open(self.RELIC_DIC_CH , "r", encoding="utf-8") as file:
            self.relic_dic_ch = json.load(file)

        #清空log
        with open(self.RELIC_LOG, "w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=4)
        
        with open(self.WISH_POOL , "r", encoding="utf-8") as file:
            tem_pool = json.load(file)
        self.pool = []
        for wish in tem_pool:
            wishes_di = {}
            must_have_li = list(wish.get("must_have", {}).keys()) if isinstance(wish.get("must_have"), dict) else []
            other_option_li = list(wish.get("other_option", {}).keys()) if isinstance(wish.get("other_option"), dict) else []
            baned_entries_li = list(wish.get("baned_entries", {}).keys()) if isinstance(wish.get("baned_entries"), dict) else []
            wishes_di["must_have"] = [int(x) for x in must_have_li]
            wishes_di["other_option"] = [int(x) for x in other_option_li]
            wishes_di["baned_entries"] = [int(x) for x in baned_entries_li]
            wishes_di["number_of_vaild_entries"] = wish["number_of_vaild_entries"]
            self.pool.append(wishes_di)


        self.eng_dic_reverse = self.dic_reverse(self.RELIC_DIC)
        # 確保資料夾存在
        self.ensure_directories()
        # print(self.SOURCE_FILE)

    def resource_path(self, relative_path):
        """取得資源路徑，支援 exe 與原始碼模式"""
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        return os.path.join(base_path, relative_path)

    def get_exe_path(self,file_name):
        """
        取得設定檔路徑：
        1. 優先讀 exe 同層的 config.yaml
        2. 如果不存在，才 fallback 到 _MEIPASS 內建
        """
        # exe 或 py 檔同層
        exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        cfg_path = os.path.join(exe_dir, file_name)
        if os.path.exists(cfg_path):
            return cfg_path

        # _MEIPASS（PyInstaller onefile 解壓縮資料夾）
        if hasattr(sys, "_MEIPASS"):
            cfg_path = os.path.join(sys._MEIPASS, file_name)
            if os.path.exists(cfg_path):
                return cfg_path

        # fallback
        return file_name

    def ensure_directories(self):
        """ 確保必要的資料夾存在 """
        os.makedirs(self.ORI_FOLDER, exist_ok=True)
        os.makedirs(self.SAVE_FOLDER, exist_ok=True)
        os.makedirs(self.SCREENSHOT_FOLDER, exist_ok=True)

    
    def save_original_file(self):
        shutil.copy2(self.SOURCE_FILE, os.path.join(self.ORI_FOLDER, "NR0000.sl2"))
        shutil.copy2(self.SOURCE_FILE_BAK, os.path.join(self.ORI_FOLDER, "NR0000.sl2.bak"))
        print("✅ 已保留最原始的檔案")

    def save_sl_file(self,filename_time):
        folder_path = os.path.join(self.SAVE_FOLDER, filename_time)
        os.makedirs(folder_path, exist_ok=True)
        shutil.copy2(self.SOURCE_FILE, os.path.join(folder_path, "NR0000.sl2"))
        shutil.copy2(self.SOURCE_FILE_BAK, os.path.join(folder_path, "NR0000.sl2.bak"))
        print("💾 已記錄存檔點")

    def recover(self):
        shutil.copy2(os.path.join(self.ORI_FOLDER, "NR0000.sl2"), self.SOURCE_FILE)
        shutil.copy2(os.path.join(self.ORI_FOLDER, "NR0000.sl2.bak"), self.SOURCE_FILE_BAK)
        print("♻️ 已恢復原始檔案")

    def restart_elden(self):
        while True:
            subprocess.run("taskkill /f /im nightreign.exe", shell=True)
            time.sleep(40)
            self.recover()
            windows = gw.getAllTitles()
            print("目前所有視窗：", windows)
            status = 0
            subprocess.Popen(self.GAME_PATH)
            print("🔄 重新啟動遊戲")
            time.sleep(20)
            for i in range(5):
                windows = gw.getAllTitles()
                if any("ELDEN RING NIGHTREIGN" in title for title in windows):
                    print('✅ 偵測到 ELDEN RING 視窗')
                    status = 1
                else:
                    print('❌沒開')
                    subprocess.Popen(self.GAME_PATH)
                    time.sleep(20)
            if status:
                elden_windows = gw.getWindowsWithTitle("ELDEN RING NIGHTREIGN")
                if not elden_windows:
                    print("❌ 無法取得 ELDEN RING 視窗對象")
                    continue

                elden = elden_windows[0]
                elden.activate()
                time.sleep(1)
                break

            print("遊戲無法開啟")
            return
        
    def image_to_text(self,img):
        image_gray = img.convert('L')
        text = pytesseract.image_to_string(image_gray)
        return text

    def text_handle(self,text):
        output_li = []
        img_str = text.splitlines()
        cleaned_lines = [line.strip() for line in img_str]

        for i in range(len(cleaned_lines)):
            if cleaned_lines[i]== "" or cleaned_lines[i]== " ":
                continue

            elif "|" in cleaned_lines[i]:
                split_line = cleaned_lines[i].split("|")
                if len(output_li) == 0:
                    output_li.append(split_line[0])
                    output_li.append(split_line[1])
                else:
                    output_li[-1] += split_line[0]
                    output_li.append(split_line[1])

            elif cleaned_lines[i][0].islower():
                if len(output_li) == 0:
                    output_li.append(cleaned_lines[i])
                else:
                    output_li[-1] += cleaned_lines[i]
            else:
                output_li.append(cleaned_lines[i])
        output_li2= []
        for i in output_li:
            
            output_li2.append(str(re.sub(r'^[^A-Za-z\[]+|[^A-Za-z\]]+$', '', i)))
        return output_li2


    def find_in_dic(self, li, di, di_ch, filename_time):
        all_key = di.keys()
        output_value_li = []
        log_li = []
        
        with open(self.RELIC_LOG, "r", encoding="utf-8") as file:
            content = json.load(file)
        
        entrys = len(li)
        ignores = False

        for j in range(entrys):
            if ignores:
                ignores = False
                continue

            # 處理字串對（當前字串和下一個字串）
            if j != entrys - 1:
                combined_key = li[j] + " " + li[j+1]
                if di.get(combined_key, False):  # 檢查合併字串是否存在
                    print(f"結合成功 直接抓到  {combined_key}") 
                    output_value_li.append(int(di.get(combined_key)))
                    log_li.append([di.get(combined_key), di_ch.get(di.get(combined_key)), filename_time])
                    ignores = True  # 跳過下一句
                elif di.get(li[j], False):  # 檢查當前字串是否存在
                    print(f"直接抓到  {li[j]}")
                    output_value_li.append(int(di.get(li[j], False)))
                    log_li.append([di.get(li[j], False), di_ch.get(di.get(li[j], False)), filename_time])
                else:  # 找不到則取最接近的字串
                    closest_match = min(all_key, key=lambda db_item: Levenshtein.distance(db_item, li[j]))
                    print(f"找不到   |{li[j]}|  {len(li[j])}")
                    print(f"最接近為  |{closest_match}|  {len(closest_match)}")
                    output_value_li.append(int(di[closest_match]))
                    log_li.append([di[closest_match], di_ch.get(di[closest_match]), filename_time])
            else:
                # 最後一個字串單獨處理
                if di.get(li[j], False):
                    print(f"直接抓到  {li[j]}")
                    output_value_li.append(int(di.get(li[j], False)))
                    log_li.append([di.get(li[j], False), di_ch.get(di.get(li[j], False)), filename_time])
                else:
                    closest_match = min(all_key, key=lambda db_item: Levenshtein.distance(db_item, li[j]))
                    print(f"找不到   |{li[j]}|  {len(li[j])}")
                    print(f"最接近為  |{closest_match}|  {len(closest_match)}")
                    output_value_li.append(int(di[closest_match]))
                    log_li.append([di[closest_match], di_ch.get(di[closest_match]), filename_time])

        # 將 log_li 排序並保存
        log_li_sorted = sorted(log_li, key=lambda x: int(x[0]))
        content.append(log_li_sorted)
        
        with open(self.RELIC_LOG, "w", encoding="utf-8") as file:
            json.dump(content, file, ensure_ascii=False, indent=4)
        
        return output_value_li


    def dic_reverse(self,dic_json):
        with open(dic_json, "r", encoding="utf-8") as file:
            ans = json.load(file)
        # print(ans)

        revered_di = {v:k for k,v in ans.items()}
        return revered_di

    def check_wish_pool(self,now_relic_li):
        print(now_relic_li)
        for wish in self.pool:
            # print(wish)
            
            must_point = False
            score = wish["number_of_vaild_entries"]

            if len(wish["must_have"]) >3:
                continue

            for i in wish["must_have"]:
                if i in now_relic_li:
                    score -= 1
                else:
                    must_point = True
                    break
            
            if must_point:
                continue

            for i in wish["baned_entries"]:
                if i in now_relic_li:
                    must_point = True
                    break
            if must_point:
                continue

            elif score != 0:
                for j in wish["other_option"]:
                    if j in now_relic_li:
                        score -= 1
            else:
                # print(wish)
                return True
            
            if score<=0:
                return True
            
        return False

    def game_start(self):
        print('進入遊戲大廳中')

        time.sleep(0.5)
        pydirectinput.moveTo(235,279)
        pydirectinput.press('f')
        time.sleep(0.5)

    def back_to_desk(self):
        print("準備返回主選單")
        pydirectinput.press('f')
        time.sleep(1)
        pydirectinput.press('q')
        time.sleep(1)
        pydirectinput.press('q')
        time.sleep(1)
        pydirectinput.press('esc')
        time.sleep(1)
        pydirectinput.press('f1')
        time.sleep(1)

        pydirectinput.press('up')
        time.sleep(1)
        pydirectinput.press('f')
        time.sleep(1)

        pydirectinput.press('f')
        time.sleep(1)

        pydirectinput.press('left')
        time.sleep(1)
        pydirectinput.press('f')
        time.sleep(10)
        return
    
    def auto_pot(self, filename_time):
        print("auto pot")
        time.sleep(1)
        pydirectinput.press('m')
        time.sleep(2)

        for i in range(6):
            pydirectinput.press('down')
            time.sleep(0.1)
        pydirectinput.press('f')
        time.sleep(4)
        pydirectinput.press('f1')
        time.sleep(0.1)

        for i in range(8):
            pydirectinput.press('down')
            time.sleep(0.1)

        pydirectinput.press('right')
        time.sleep(0.1)
        
        pydirectinput.press('f')
        time.sleep(0.5)
        for i in range(self.MOD_MANY-1):
            pydirectinput.press('up')
        pydirectinput.press('f')
        time.sleep(0.5)
        reset_ori = False
        time.sleep(2)
        for i in range(self.MOD_MANY):
            time.sleep(0.5)
            screenshot = pyautogui.screenshot(region=(self.REGION['x'], self.REGION['y'], self.REGION['width'], self.REGION['height']))
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}_0"+".png"
            screenshot.save(save_path)
            text = self.image_to_text(screenshot)
            new_text = self.text_handle(text)
            
            now_relic = self.find_in_dic(new_text,self.eng_dic_reverse,self.relic_dic_ch,filename_time)
            check_keep = self.check_wish_pool( now_relic_li = now_relic)

            screenshot2 = pyautogui.screenshot()
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}"+".png"
            screenshot2.save(save_path)

            if check_keep:
                pydirectinput.press('2')
                time.sleep(0.5)
                
                pydirectinput.press('right')
                time.sleep(0.5)
                self.PEEK-=1
                if self.PEEK == 0:
                    input("已到達抽取數量 按任意鍵終止")
                    sys.exit()
                reset_ori = True
            else:
                pydirectinput.press('3')
                time.sleep(0.5)
        if self.AUTO_SELL == 'y':
            if reset_ori:
                print("恭喜取得好遺物，已刪除無用遺物")
            else:
                pydirectinput.press('1')
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        else:
            pydirectinput.press('1')
            if reset_ori:
                print("恭喜取得好遺物，保留完整抽取內容")
            else:
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        return reset_ori
    
    def auto_board(self, filename_time):
        print("auto board")
        time.sleep(1)
        pydirectinput.press('m')
        time.sleep(2)

        for i in range(7):
            pydirectinput.press('down')
            time.sleep(0.1)

        pydirectinput.press('f')
        time.sleep(5)

        pydirectinput.press('f')
        time.sleep(1)

        pydirectinput.press('f2')
        time.sleep(0.5)

        pydirectinput.press('f2')
        time.sleep(0.5)

        for i in range(6):
            pydirectinput.press('down')
            time.sleep(0.2)
        
        pydirectinput.press('f')
        time.sleep(0.5)
        for i in range(self.MOD_MANY-1):
            pydirectinput.press('up')
        pydirectinput.press('f')
        time.sleep(0.5)
        reset_ori = False
        time.sleep(2)
        for i in range(self.MOD_MANY):
            time.sleep(0.5)
            screenshot = pyautogui.screenshot(region=(self.REGION['x'], self.REGION['y'], self.REGION['width'], self.REGION['height']))
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}_0"+".png"
            screenshot.save(save_path)
            text = self.image_to_text(screenshot)
            new_text = self.text_handle(text)
            
            now_relic = self.find_in_dic(new_text,self.eng_dic_reverse,self.relic_dic_ch,filename_time)
            check_keep = self.check_wish_pool( now_relic_li = now_relic)

            screenshot2 = pyautogui.screenshot()
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}"+".png"
            screenshot2.save(save_path)

            if check_keep:
                pydirectinput.press('2')
                time.sleep(0.5)
                
                pydirectinput.press('right')
                time.sleep(0.5)
                self.PEEK-=1
                if self.PEEK == 0:
                    input("已到達抽取數量 按任意鍵終止")
                    sys.exit()
                reset_ori = True
            else:
                pydirectinput.press('3')
                time.sleep(0.5)
        if self.AUTO_SELL == 'y':
            if reset_ori:
                print("恭喜取得好遺物，已刪除無用遺物")
            else:
                pydirectinput.press('1')
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        else:
            pydirectinput.press('1')
            if reset_ori:
                print("恭喜取得好遺物，保留完整抽取內容")
            else:
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        return reset_ori


    def auto_pot_general(self, filename_time):
        print("auto pot general")
        time.sleep(1)
        pydirectinput.press('m')
        time.sleep(2)

        for i in range(6):
            pydirectinput.press('down')
            time.sleep(0.1)
        pydirectinput.press('f')
        time.sleep(4)
        pydirectinput.press('f1')
        time.sleep(0.1)

        for i in range(8):
            pydirectinput.press('down')
            time.sleep(0.1)


        
        pydirectinput.press('f')
        time.sleep(0.5)
        for i in range(self.MOD_MANY-1):
            pydirectinput.press('up')
        pydirectinput.press('f')
        time.sleep(0.5)
        reset_ori = False
        time.sleep(2)
        for i in range(self.MOD_MANY):
            time.sleep(0.5)
            screenshot = pyautogui.screenshot(region=(self.REGION['x'], self.REGION['y'], self.REGION['width'], self.REGION['height']))
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}_0"+".png"
            screenshot.save(save_path)
            text = self.image_to_text(screenshot)
            new_text = self.text_handle(text)
            
            now_relic = self.find_in_dic(new_text,self.eng_dic_reverse,self.relic_dic_ch,filename_time)
            check_keep = self.check_wish_pool( now_relic_li = now_relic)

            screenshot2 = pyautogui.screenshot()
            save_path = self.SCREENSHOT_FOLDER + "\\" + str(filename_time) + f"_{i}"+".png"
            screenshot2.save(save_path)
            if check_keep:
                pydirectinput.press('2')
                time.sleep(0.5)
                
                pydirectinput.press('right')
                time.sleep(0.5)
                self.PEEK-=1
                if self.PEEK == 0:
                    input("已到達抽取數量 按任意鍵終止")
                    sys.exit()
                reset_ori = True
            else:
                pydirectinput.press('3')
                time.sleep(0.5)
        if self.AUTO_SELL == 'y':
            if reset_ori:
                print("恭喜取得好遺物，已刪除無用遺物")
            else:
                pydirectinput.press('1')
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        else:
            pydirectinput.press('1')
            if reset_ori:
                print("恭喜取得好遺物，保留完整抽取內容")
            else:
                print("沒有好遺物，已儲存完整抽取內容，準備回檔")
        return reset_ori

    def load_sl_file(self,file_name,CLEAR_FILE):
        print("正在load存檔")
        folders = os.listdir(self.SAVE_FOLDER)
        
        exit_mux = False
        if file_name != "":
            if file_name in folders:
                save_folder = os.path.join(self.SAVE_FOLDER, file_name)
                file1 = os.path.join(save_folder, "NR0000.sl2")
                file2 = os.path.join(save_folder, "NR0000.sl2.bak")

                shutil.copy2(file1, self.SOURCE_FILE)
                shutil.copy2(file2, self.SOURCE_FILE_BAK)
                print('已選擇存檔點')
                exit_mux = True

        if CLEAR_FILE == "y":
            #清空
            folder = self.SAVE_FOLDER

            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)  # 刪除檔案或符號連結
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # 遞迴刪除資料夾
                except Exception as e:
                    print(f"⚠️ 無法刪除 {file_path}: {e}")

            print("✅ 已清空資料夾內容")
            folder = self.SCREENSHOT_FOLDER

            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)  # 刪除檔案或符號連結
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # 遞迴刪除資料夾
                except Exception as e:
                    print(f"⚠️ 無法刪除 {file_path}: {e}")

            print("✅ 已清空資料夾內容")

            self.config["sl_file"] = ""
            self.config["clear_file"] = "y"
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                self.rua_yaml.dump(self.config, f)
            
            if exit_mux:
                input("✅ 已讀取 sl_file  輸入任意鍵終止")
                sys.exit()
        else:
            input("找不到檔案  輸入任意鍵終止")
            
        return
    
    def main(self):
        self.load_sl_file(self.SL_FILE,self.CLEAR_FILE)

        pydirectinput.FAILSAFE = False
        self.save_original_file()

        while True:
            error_count = 0
            filename_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # detect_elden()

            while True:
                elden_windows = gw.getWindowsWithTitle("ELDEN RING NIGHTREIGN")
                if not elden_windows:
                    print("❌ 無法取得 ELDEN RING 視窗對象")
                    
                    subprocess.Popen(self.GAME_PATH)
                    print('正在開啟黑環')
                    time.sleep(10)
                    continue
                elden = elden_windows[0]
                elden.activate()
                time.sleep(1)

                try:
                    time.sleep(2)
                    to_board_check = pyautogui.locateOnScreen(self.IMAGES['home'], grayscale=True, confidence=0.6)
                    
                    if to_board_check is not None:
                        print("✅ 偵測到 home.png，結束迴圈")
                        break

                except Exception as ex:
                    # print(f"⚠️ 進入home出現錯誤。執行 game_start() 錯誤 {error_count} 次")
                    error_count += 1
                    if error_count >= 40:
                        self.restart_elden()
                        break
                    self.game_start()


            if error_count >= 40:
                continue
            else :
                error_count = 0 



            time.sleep(2)
            auto_reset = False
            board_error = False
            pytesseract.pytesseract.tesseract_cmd = self.OCR_PATH
            
            if self.MOD_TYPE == 1:
                if self.MOD_MANY<1 or self.MOD_MANY>10:
                    input("抽取數量錯誤")
                    sys.exit()
                else:
                    auto_reset = self.auto_pot(filename_time)
            
            elif self.MOD_TYPE == 2:
                if self.MOD_MANY<1 or self.MOD_MANY>10:
                    input("抽取數量錯誤")
                    sys.exit()
                else:
                    auto_reset = self.auto_board(filename_time)
            elif self.MOD_TYPE == 3:
                if self.MOD_MANY<1 or self.MOD_MANY>10:
                    input("抽取數量錯誤")
                    sys.exit()
                else:
                    auto_reset = self.auto_pot_general(filename_time)
            else :
                input("mod 錯誤 請ctrl+c終止並調整mod後重新開始")
            time.sleep(2)

                
            if board_error:
                self.restart_elden()
                continue

            self.back_to_desk()
            time.sleep(1.5)
            self.save_sl_file(filename_time) 
            print("round:  "+ str(filename_time)+ "  over")
            if auto_reset:
                self.save_original_file()
            else:
                self.recover()
            print("recover 原檔結束，可暫停")
            time.sleep(5)
            
            
        
        # mouse_position()
def get_log_path():
    """ 根據執行模式確定 log 檔案的儲存路徑 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller onefile 模式
        base_path = sys._MEIPASS
    else:
        # 原始碼或 onedir 模式
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 設定 log 檔案名稱為 log.txt，並確保它位於 exe 同一層目錄
    return os.path.join(base_path, "log.txt")

if __name__ == '__main__':
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:  # 以追加模式寫入
            f.write(f"[{ts}]")
        config_manager = ConfigManager()
        
        config_manager.main()
    except Exception as ex:
        
        print(ex)
        with open(log_path, "a", encoding="utf-8") as f:  # 以追加模式寫入
            f.write(f"[{ts}] {ex.__class__.__name__}: {ex}\n")
            f.write(traceback.format_exc())
            f.write("\n" + "-"*80 + "\n")
        input(f"⚠️ 發生例外，詳見：{log_path}")
        
 

