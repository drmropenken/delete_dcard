# delete_dcard

本專案包含 4 支 Dcard 自動刪除腳本，用於自動登入 Dcard 並刪除文章或留言。專案核心仍維持原始邏輯，僅補充必要的設定檔與說明。

## 檔案結構

- `delete_article.py`：刪除所有文章。
- `delete_article_with_name.py`：刪除指定名稱身分下的文章。
- `delete_message.py`：刪除所有留言。
- `delete_message_with_name.py`：刪除指定名稱身分下的留言。
- `auth.json`：Playwright 登入狀態儲存檔，**不應上傳到 GitHub**。
- `environment.yml`：Conda 環境建置檔。
- `requirements.txt`：pip 套件需求檔。
- `.gitignore`：忽略本機暫存檔與 `auth.json`。

## 使用環境

- Python 3.12
- Conda 環境名稱：`myenv`
- Playwright 1.60.0

## 快速安裝

建議使用 Conda 建立環境：

```bash
conda env create -f environment.yml
conda activate myenv
```

安裝完成後，請安裝 Playwright 的瀏覽器：

```bash
playwright install chrome
```

如果你只有 `pip` 需求，也可以直接：

```bash
pip install -r requirements.txt
playwright install chrome
```

## 重要提醒

- `auth.json` 包含你的 Dcard session cookies / localStorage，請務必不要上傳到 GitHub。這個檔案已經加入 `.gitignore`。
- 若你要重新登入，執行腳本時加上 `--fresh` 參數，會忽略既有 `auth.json`，重新開啟瀏覽器讓你手動登入。

## 執行方式

在專案目錄中執行：

```bash
cd /Users/chun-chiehchin/WorkingSpace/delete_dcard
conda activate myenv
python delete_article.py
python delete_article.py --fresh
python delete_article_with_name.py --persona-name "Trash TSMC"
python delete_article_with_name.py --fresh --persona-name "Trash TSMC"
python delete_message.py
python delete_message.py --fresh
python delete_message_with_name.py --persona-name "Trash TSMC"
python delete_message_with_name.py --fresh --persona-name "Trash TSMC"
```

如果你使用其他 persona 名稱，請把 `--persona-name` 後面的值改成你自己的名稱。

如果 Dcard 網址將來有變動，請檢查並更新程式碼中的 `persona_url` / `comments_url` 變數值。
## 注意事項

- 因為 Dcard 網站會變動，執行時若定位器找不到對應按鈕，腳本會顯示錯誤並嘗試跳過該條目。
- 目前 `auth.json` 只會保存在本機，GitHub 上只需要上傳程式與說明文件。
