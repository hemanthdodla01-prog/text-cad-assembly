import urllib.parse
from playwright.sync_api import sync_playwright

_playwright = None
_browser = None
_page = None


def get_page():
    """Initializes or restores the active Playwright browser tab safely."""
    global _playwright, _browser, _page

    need_new_page = False
    if _page is None:
        need_new_page = True
    else:
        try:
            if _page.is_closed():
                need_new_page = True
        except Exception:
            need_new_page = True

    if need_new_page:
        if _playwright is None:
            _playwright = sync_playwright().start()

        _browser = _playwright.chromium.launch(
            headless=False, args=["--start-maximized"]
        )
        context = _browser.new_context(no_viewport=True)
        _page = context.new_page()

    return _page


def open_youtube():
    try:
        page = get_page()
        page.goto("https://www.youtube.com")
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error opening YouTube: {e}")


def search_youtube(query: str):
    try:
        page = get_page()
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        page.goto(search_url)
        page.wait_for_selector("ytd-video-renderer", timeout=10000)
        page.click("ytd-video-renderer #video-title")
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error during YouTube search: {e}")


def open_instagram():
    try:
        page = get_page()
        page.goto("https://www.instagram.com")
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error opening Instagram: {e}")


def open_chatgpt():
    try:
        page = get_page()
        page.goto("https://chatgpt.com")
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error opening ChatGPT: {e}")


def open_gmail():
    try:
        page = get_page()
        page.goto("https://mail.google.com")
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error opening Gmail: {e}")


def open_website(site_input: str):
    """Opens any website URL or navigates via Google for general terms."""
    try:
        page = get_page()
        site_input = site_input.strip()

        # Check if it's already a full URL or domain (e.g. github.com, reddit.com)
        if site_input.startswith("http://") or site_input.startswith("https://"):
            target_url = site_input
        elif "." in site_input and " " not in site_input:
            target_url = f"https://{site_input}"
        else:
            # For queries like "seiko", "ethos watches", or "netflix"
            encoded = urllib.parse.quote(site_input)
            target_url = f"https://www.google.com/search?q={encoded}"

        page.goto(target_url)
        page.bring_to_front()
    except Exception as e:
        print(f"Browser error opening website: {e}")