import re
import urllib.request
import base64

GITHUB_SOURCES = [
    "".join(["https://", "raw.github", "usercontent.com", "/mehrtat", "/vless-collector", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/yebekhe", "/TVC", "/main", "/protocols", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Satbashi", "/抽屉", "/master", "/vless.txt"])
]

TELEGRAM_CHANNELS = [
    "v2ray_outline_vless_vmess",
    "FreeVlessVmessOutline",
    "vless_vmess_ss_shadowsocks",
    "nufilter",
    "V2Ray_Alpha"
]

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore').strip()
    except:
        return ""

def decode_base64_if_needed(text):
    if "vless://" in text or "vmess://" in text or "ss://" in text:
        return text
    try:
        padded_text = text + "=" * ((4 - len(text) % 4) % 4)
        return base64.b64decode(padded_text).decode('utf-8', errors='ignore')
    except:
        return text

def extract_vless(text):
    pattern = r"vless://[^\"'\s<>\s]+"
    return re.findall(pattern, text)

def main():
    all_vless_links = []
    
    # Сбор с GitHub
    for source in GITHUB_SOURCES:
        content = fetch_url(source)
        if content:
            links = extract_vless(decode_base64_if_needed(content))
            all_vless_links.extend(links)
            
    # Сбор с Telegram
    for channel in TELEGRAM_CHANNELS:
        slash = chr(47)
        tg_url = "".join(["https:", slash, slash, "telemetr.", "me", slash, "r", slash, channel])
        html_content = fetch_url(tg_url)
        if not html_content:
            tg_url = "".join(["https:", slash, slash, "t.me", slash, "s", slash, channel])
            html_content = fetch_url(tg_url)
        if html_content:
            all_vless_links.extend(extract_vless(html_content))
            
    unique_links = list(dict.fromkeys(all_vless_links))
    
    if unique_links:
        # 1. Сохраняем обычный текст для бота
        raw_text = "\n".join(unique_links)
        with open("vless_proxies.txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
            
        # 2. Сохраняем Base64 подписку для v2rayN/NekoBox
        base64_sub = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write(base64_sub)
            
        print(f"Успешно обновлено! Собрано прокси: {len(unique_links)}")

if __name__ == "__main__":
    main()
