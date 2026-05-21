"""delete_article.py – 使用 Playwright 自動登入 Dcard 並刪除所有文章

此腳本會在第一次執行時要求手動登入，之後會把瀏覽器的 session
(cookies、localStorage 等) 儲存至同目錄下的 ``auth.json``，未來再執行
時會直接載入該檔案，避免再次輸入帳號密碼。

使用方式：
    conda run -n myenv python delete_dcard/delete_article.py [--fresh]

* ``--fresh``：忽略已存在的 ``auth.json``，重新開啟瀏覽器讓使用者手動登入。
"""

import argparse
import os
from typing import Tuple

from playwright.sync_api import BrowserContext, Page, sync_playwright


def _init_browser(p, auth_path: str, fresh: bool) -> Tuple[BrowserContext, bool]:
    """建立瀏覽器與 context，根據是否已有 session 決定是否載入。

    Returns:
        (context, use_saved_session)
    """
    browser = p.chromium.launch(
        headless=False,
        channel="chrome",
        ignore_default_args=["--enable-automation"],
        args=["--start-maximized"],
    )
    if os.path.exists(auth_path) and not fresh:
        context = browser.new_context(storage_state=auth_path, no_viewport=True)
        print(f"【成功】已從 {auth_path} 載入登入狀態。")
        use_saved = True
    else:
        context = browser.new_context(no_viewport=True)
        print("【提示】啟動全新視窗，請先手動登入。")
        use_saved = False
    # 繞過 webdriver 檢查
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """
    )
    return context, use_saved


def _ensure_logged_in(
    context: BrowserContext, page: Page, auth_path: str, use_saved: bool
) -> None:
    """若是第一次執行，等待使用者手動登入並儲存 session。"""
    if not use_saved:
        print("\n==================================================")
        print(
            "【操作指引】請先在瀏覽器手動登入，完成後回到這裡按 [Enter] 開始自動刪除..."
        )
        print("==================================================\n")
        input()
        context.storage_state(path=auth_path)
        print(f"【已儲存】登入狀態已寫入 {auth_path}")


def _delete_single_article(page: Page, persona_url: str) -> bool:
    """刪除單篇文章，成功刪除回傳 True，失敗回傳 False。

    Args:
        page: Playwright 頁面物件
        persona_url: Dcard 個人主頁 URL

    Returns:
        bool: 是否成功刪除
    """
    # 確保回到主頁面
    if page.url != persona_url:
        print("【導向】回到個人文章主頁...")
        page.goto(persona_url)
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

    # 找到第一篇文章
    first_article = page.locator("article").first
    if not first_article.is_visible():
        return False

    try:
        # 1. 點擊文章進入詳細頁面
        print("【執行】正在點擊並跳轉至文章...")
        article_link = first_article.locator('a[href*="/p/"]').first
        if article_link.is_visible():
            article_link.click()
        else:
            first_article.click()
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

        # 2. 點擊編輯按鈕
        edit_btn = page.locator('button[aria-label="edit"]').first
        if not edit_btn.is_visible():
            print("【警告】找不到編輯按鈕，跳過此篇。")
            return False

        edit_btn.click()
        print("【動作】已點擊編輯按鈕。")
        page.wait_for_timeout(800)

        # 3. 點擊刪除選項
        delete_menu_item = page.locator('text="刪除文章"').first
        if not delete_menu_item.is_visible():
            delete_menu_item = page.locator(
                'span:has-text("刪除文章"), button:has-text("刪除文章")'
            ).first
        delete_menu_item.click()
        print("【動作】已點擊「刪除文章」選項。")
        page.wait_for_timeout(1000)

        # 4. 確認刪除
        confirm_btn = page.locator(
            'div[role="dialog"] button:has-text("刪除"), button:has-text("刪除")'
        ).last
        confirm_btn.click()

        print("🎉 成功刪除一篇文章")
        page.wait_for_timeout(2000)
        return True

    except Exception as e:
        print(f"【錯誤】刪除文章時發生異常: {e}")
        return False


def _delete_all_articles(page: Page, persona_url: str) -> int:
    """在 Dcard 個人頁面上逐筆刪除文章，回傳刪除總數。"""
    deleted = 0
    while True:
        if not _delete_single_article(page, persona_url):
            # 如果刪失敗，嘗試重整頁面
            print("【提示】找不到文章，嘗試重整...")
            page.reload()
            page.wait_for_load_state("load")
            page.wait_for_timeout(2000)
            if not _delete_single_article(page, persona_url):
                print("【結束】找不到任何文章，全數刪除完畢！")
                break
        deleted += 1
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open Dcard persona page and auto‑delete all articles."
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing auth.json and start a fresh browser session.",
    )
    args = parser.parse_args()

    auth_path = os.path.join(os.path.dirname(__file__), "auth.json")
    persona_url = "https://www.dcard.tw/my/persona"

    with sync_playwright() as p:
        context, use_saved = _init_browser(p, auth_path, args.fresh)
        page = context.new_page()
        page.goto(persona_url)
        page.wait_for_load_state("load")

        _ensure_logged_in(context, page, auth_path, use_saved)

        print("【開始執行】正在偵測文章狀態...")
        deleted = _delete_all_articles(page, persona_url)
        context.storage_state(path=auth_path)
        print(f"【大功告成】本次執行共刪除了 {deleted} 篇文章！")
        context.browser.close()


if __name__ == "__main__":
    main()
