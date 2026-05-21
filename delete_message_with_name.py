"""delete_message_with_name.py – 使用 Playwright 自動登入 Dcard 並刪除指定名稱的所有留言

此腳本會在第一次執行時要求手動登入，之後會把瀏覽器的 session
(cookies、localStorage 等) 儲存至同目錄下的 ``auth.json``，未來再執行
時會直接載入該檔案，避免再次輸入帳號密碼。

使用方式：
    conda run -n myenv python delete_dcard/delete_message_with_name.py [--fresh] [--persona-name "Your Name"]

* ``--fresh``：忽略已存在的 ``auth.json``，重新開啟瀏覽器讓使用者手動登入。
* ``--persona-name``：指定要切換的 Dcard persona 名稱，預設為 ``Trash TSMC``。
"""

import argparse
import os
import re
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


def _switch_to_persona_page(page: Page, persona_name: str) -> None:
    """切換到指定名稱的個人頁面。"""
    # 尋找內文含有 persona_name 的那個最外層身分卡片 div，並點擊它
    persona_card = (
        page.locator(f'div:has-text("{persona_name}")')
        .filter(has=page.locator('div[style*="pointer"]'))
        .first
    )

    # 或者更精準的寫法（直接定位最外層，並限定內部文字）：
    if not persona_card.is_visible():
        persona_card = page.locator(f'div.d_12rlolc:has-text("{persona_name}")').first

    if persona_card.is_visible():
        persona_card.click()
        page.wait_for_timeout(500)
        # 抓取畫面上文字為「回覆」的第一個按鈕
        reply_btn = page.locator('button:has-text("回覆")').first
        if reply_btn.is_visible():
            reply_btn.click()
        else:
            print("【提示】未找到回覆按鈕，可能已經在正確頁面。")
    else:
        print(f"【警告】找不到名稱為 '{persona_name}' 的卡片，使用預設留言頁面。")


def _delete_single_comment(page: Page) -> bool:
    """刪除單則留言，成功刪除回傳 True，失敗回傳 False。

    Args:
        page: Playwright 頁面物件

    Returns:
        bool: 是否成功刪除
    """
    # 找到第一個「更多」按鈕
    more_btn = page.locator('button[title="more"], button[title="更多"]').first
    if not more_btn.is_visible():
        return False

    try:
        # 1. 點擊三個點（更多）
        more_btn.click()
        page.wait_for_timeout(600)

        # 2. 點擊彈出選單中的「刪除」項目
        delete_menu_item = page.locator(
            'div[role="dialog"] button, [role="dialog"] button'
        ).first
        delete_menu_item.click()
        page.wait_for_timeout(800)

        # 3. 點擊最後大確認彈窗裡面的「刪除」確認紅鈕
        confirm_btn = page.locator(
            'button:has-text("刪除"), div[role="dialog"] button >> text="刪除"'
        ).last
        confirm_btn.click()

        print("🎉 成功刪除一則留言")
        page.wait_for_timeout(1500)
        return True

    except Exception as e:
        print(f"【錯誤】刪除留言時發生異常: {e}")
        return False


def _delete_all_comments(page: Page) -> int:
    """在 Dcard 個人留言頁面上逐筆刪除留言，回傳刪除總數。"""
    deleted = 0
    while True:
        # 檢查是否有「更多」按鈕
        more_btn = page.locator('button[title="more"], button[title="更多"]').first
        if not more_btn.is_visible():
            # 捲回最上方重新整理，確保沒有遺漏的留言
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1500)
            page.reload()
            page.wait_for_load_state("load")
            page.wait_for_timeout(3000)
            # 再次檢查
            more_btn = page.locator('button[title="more"], button[title="更多"]').first
            if not more_btn.is_visible():
                print("【結束】找不到任何留言的三個點按鈕，全數刪除完畢！")
                break

        if not _delete_single_comment(page):
            # 如果刪失敗，嘗試重整頁面
            print("【提示】刪除失敗，嘗試重整...")
            page.reload()
            page.wait_for_load_state("load")
            page.wait_for_timeout(2500)
        else:
            deleted += 1
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open Dcard comments page and auto‑delete all comments."
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore existing auth.json and start a fresh browser session.",
    )
    parser.add_argument(
        "--persona-name",
        default="Trash TSMC",
        help="The Dcard persona display name to select, e.g. your personal identity name.",
    )
    args = parser.parse_args()

    auth_path = os.path.join(os.path.dirname(__file__), "auth.json")
    comments_url = "https://www.dcard.tw/my/persona?tab=comments"
    # 如果 Dcard 的留言頁面網址未來變動，可在此修改。

    with sync_playwright() as p:
        context, use_saved = _init_browser(p, auth_path, args.fresh)
        page = context.new_page()
        page.goto(comments_url)
        page.wait_for_load_state("load")

        _ensure_logged_in(context, page, auth_path, use_saved)

        print("【開始執行】正在偵測留言總數...")
        page.wait_for_selector("text=全部")

        # 偵測目前還有幾篇要刪除（解析例如 "全部 (3912)" 裡面的數字）
        try:
            total_text = page.locator(
                "xpath=//*[contains(text(), '全部')]"
            ).first.inner_text()
            match = re.search(r"\d+", total_text)
            if match:
                print(f"【偵測成功】目前剩餘留言總數約為：{match.group()} 則")
        except Exception:
            print("【無法確認總數】將直接開始依序刪除。")

        # 切換到個人名稱頁面，因為有些人是沒有公開文章的，只有留言在個人名稱頁面才看得到
        _switch_to_persona_page(page, args.persona_name)

        deleted = _delete_all_comments(page)
        context.storage_state(path=auth_path)
        print(f"【大功告成】本次執行共刪除了 {deleted} 則留言！")
        context.browser.close()


if __name__ == "__main__":
    main()
