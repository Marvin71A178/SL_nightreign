@echo off
REM ========= PyInstaller Build Script =========
set NAME=SL_NIGHTREIGN

echo 🔄 清理舊的 build 和 dist...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del %NAME%.spec 2>nul

echo 🚀 開始打包...
python -m PyInstaller main.py ^
  --name %NAME% ^
  --onedir ^
  --console ^
  --add-data "config.yaml;." ^
  --add-data "asset;asset" ^
  --add-data "ori;ori" ^
  --add-data "save_folder;save_folder" ^
  --add-data "screen_shot;screen_shot" ^
  --add-data "relic_dic_ch.json;." ^
  --add-data "relic_dic.json;." ^
  --add-data "wish_pool.json;." ^
  --add-data "relic_log.json;."

echo 📂 確保 config.yaml 存在於 dist\%NAME%...
if not exist dist\%NAME%\config.yaml (
    copy config.yaml dist\%NAME%\
    echo ⚠️ hand copy config.yaml
) else (
    echo ✅ correct config.yaml
)
echo 📂 確保 relic_log.json 存在於 dist\%NAME%...
if not exist dist\%NAME%\relic_log.json (
    copy relic_log.json dist\%NAME%\
    echo ⚠️ hand copy relic_log.json
) else (
    echo ✅ correct relic_log.json
)
echo 📂 確保 wish_pool.json 存在於 dist\%NAME%...
if not exist dist\%NAME%\wish_pool.json (
    copy wish_pool.json dist\%NAME%\
    echo ⚠️ hand copy wish_pool.json
) else (
    echo ✅ correct wish_pool.json
)
echo 📂 確保 config.yaml 存在於 dist\%NAME%...
if not exist dist\%NAME%\config.yaml (
    copy config.yaml dist\%NAME%\
    echo ⚠️ hand copy config.yaml
) else (
    echo ✅ correct config.yaml
)
echo.
echo 🎉 打包完成！
echo 輸出目錄: dist\%NAME%
pause
