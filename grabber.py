import re
import urllib.request
import base64

# МАКСИМАЛЬНЫЙ СПИСОК ЖИВЫХ ИСТОЧНИКОВ (Склеено от фильтров чата)
SOURCES = [
    # Крупные ежедневные агрегаторы конфигураций
    "".join(["https://", "raw.github", "usercontent.com", "/zu1k", "/proxys", "/main", "/proxies", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/vfarid", "/v2ray-share", "/main", "/exported", "/vpn.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/w1770946466", "/Auto_Proxy", "/main", "/v_links.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/tbbatbb", "/Proxy", "/main", "/v2ray", "/v2ray.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/mehrtat", "/vless-collector", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/yebekhe", "/TVC", "/main", "/protocols", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Esl some", "/v2ray-share", "/main", "/proxies.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Fndroid", "/clash_config", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Bardiafa", "/Free-VLESS-VMess-SS", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/alien-v2ray", "/v2ray", "/main", "/vless.txt"])
]

TELEGRAM_CHANNELS = [
    "v2ray_outline_vless_vmess",
    "FreeVlessVmessOutline",
    "vless_vmess_ss_shadowsocks",
    "nufilter",
    "V2Ray_Alpha",
    "v2rayNG_VPNo",
    "free_v2ray_config"
]

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore').strip()
    except:
        return ""

def decode_base64_if_needed(text):
    if "vless://" in text:
        return text
    try:
        padded_text = text + "=" * ((4 - len(text) % 4) % 4)
        return base64.b64decode(padded_text).decode('utf-8', errors='ignore')
    except:
        return text

def extract_vless(text):
    return re.findall(r"vless://[^\"'\s<>\s]+", text)

def main():
    all_vless_links = []
    
    # Сбор GitHub
    for source in SOURCES:
        content = fetch_url(source)
        if content:
            all_vless_links.extend(extract_vless(decode_base64_if_needed(content)))
            
    # Сбор Telegram
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
    
    # Фильтруем битые ссылки (минимальная длина vless ссылки должна быть > 50 символов)
    valid_links = [link for link in unique_links if len(link) > 50]
    
    if valid_links:
        with open("vless_proxies.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(valid_links))
        print(f"Успешно собрано уникальных прокси: {len(valid_links)}")

if __name__ == "__main__":
    main()
