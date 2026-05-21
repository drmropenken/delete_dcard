# delete_dcard

批次刪除 Dcard 文章與留言的 Python / Playwright 自動化工具。適合需要清理自己帳號內容、刪除 Dcard 發文、批次刪除 Dcard 留言，或管理不同 Dcard 身分文章與留言的使用者。

Batch delete Dcard posts and comments with Python and Playwright. This tool helps automate deleting your own Dcard articles, comments, and persona-specific content after manual login.

本專案包含 4 支 Playwright 腳本，可協助使用者自動登入 Dcard，並批次刪除自己帳號下的文章或留言。

> 注意：刪除文章與留言通常無法復原。請只在自己的帳號與自己有權處理的內容上使用，並自行確認是否符合 Dcard 服務條款與相關規範。本專案與 Dcard 官方無關。

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
- 每次開始刪除前，程式會要求輸入 `DELETE` 進行二次確認。若你已確認要在自動化流程中略過確認，可以加上 `--yes`。
- 第一次測試建議先加 `--limit 1`，確認刪除範圍正確後再移除上限。

## 執行方式

在專案目錄中執行：

```bash
conda activate myenv
python delete_article.py --limit 1
python delete_article.py --fresh --limit 1
python delete_article.py --yes

python delete_article_with_name.py --persona-name "你的身分名稱" --limit 1
python delete_article_with_name.py --fresh --persona-name "你的身分名稱" --limit 1
python delete_article_with_name.py --persona-name "你的身分名稱" --yes

python delete_message.py --limit 1
python delete_message.py --fresh --limit 1
python delete_message.py --yes

python delete_message_with_name.py --persona-name "你的身分名稱" --limit 1
python delete_message_with_name.py --fresh --persona-name "你的身分名稱" --limit 1
python delete_message_with_name.py --persona-name "你的身分名稱" --yes
```

`--persona-name` 請填入你在 Dcard 個人頁面看到的身分名稱。

如果 Dcard 網址將來有變動，請檢查並更新程式碼中的 `persona_url` / `comments_url` 變數值。

## 注意事項

- 因為 Dcard 網站會變動，執行時若定位器找不到對應按鈕，腳本會顯示錯誤並嘗試跳過該條目。
- 目前 `auth.json` 只會保存在本機，GitHub 上只需要上傳程式與說明文件。
- 指定身分名稱的留言腳本若找不到該身分，會直接停止，避免刪到非預期範圍。

## 上傳 GitHub 前檢查

```bash
git status --short
git ls-files
git check-ignore -v auth.json
python -m py_compile delete_article.py delete_article_with_name.py delete_message.py delete_message_with_name.py
```

確認 `git ls-files` 沒有出現 `auth.json` 後，再建立 GitHub repository 並 push。
