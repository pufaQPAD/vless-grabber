import re
import urllib.request
import base64
import urllib.parse
import socket
import ssl
import concurrent.futures

SOURCES = [
    "".join(["https://", "raw.github", "usercontent.com", "/zu1k", "/proxys", "/main", "/proxies", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/vfarid", "/v2ray-share", "/main", "/exported", "/vpn.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/w1770946466", "/Auto_Proxy", "/main", "/v_links.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/tbbatbb", "/Proxy", "/main", "/v2ray", "/v2ray.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/mehrtat", "/vless-collector", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/yebekhe", "/TVC", "/main", "/protocols", "/vless"]),
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
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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

def parse_vless_target(link):
    """Парсит из ссылки домен/IP, порт и SNI для проверки"""
    try:
        cleaned_link = link.split('#')[0].strip()
        url_parsed = urllib.parse.urlparse(cleaned_link)
        netloc = url_parsed.netloc
        
        if "@" in netloc:
            endpoint = netloc.split("@")[1]
        else:
            endpoint = netloc
            
        if ":" in endpoint:
            host, port = endpoint.split(":")
            port = int(port)
        else:
            host = endpoint
            port = 443
            
        query = urllib.parse.parse_qs(url_parsed.query)
        sni = query.get('sni', [host])[0]
        
        return host, port, sni
    except:
        return None

def check_tls_handshake(link):
    """Проверяет доступность порта и базовый TLS Handshake"""
    target = parse_vless_target(link)
    if not target:
        return None
        
    host, port, sni = target
    
    try:
        # 1. Быстрая проверка TCP порта
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.5)
        
        # 2. Обертка в TLS (имитируем первичный хэндшейк клиента)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        secure_sock = context.wrap_socket(sock, server_hostname=sni)
        secure_sock.connect((host, port))
        secure_sock.close()
        
        return link # Сервер ответил на TLS запрос, он живой
    except:
        return None # Сервер мертв или заблокирован

def main():
    print("📥 Сбор прокси со всех источников...")
    all_vless_links = []
    
    for source in SOURCES:
        content = fetch_url(source)
        if content:
            all_vless_links.extend(re.findall(r"vless://[^\"'\s<>\s]+", decode_base64_if_needed(content)))
            
    for channel in TELEGRAM_CHANNELS:
        slash = chr(47)
        tg_url = "".join(["https:", slash, slash, "telemetr.", "me", slash, "r", slash, channel])
        html_content = fetch_url(tg_url)
        if not html_content:
            tg_url = "".join(["https:", slash, slash, "t.me", slash, "s", slash, channel])
            html_content = fetch_url(tg_url)
        if html_content:
            all_vless_links.extend(re.findall(r"vless://[^\"'\s<>\s]+", html_content))
            
    unique_links = list(dict.fromkeys([l for l in all_vless_links if len(l) > 50]))
    print(f"📊 Всего собрано из сети: {len(unique_links)} шт. Начинаем TLS-валидацию...")
    
    # Запускаем проверку в 50 параллельных потоков (мгновенный чекер)
    working_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_tls_handshake, unique_links)
        for res in results:
            if res:
                working_links.append(res)
                
    print(f"✅ Проверку прошли (живые TLS порты): {len(working_links)} из {len(unique_links)}")
    
    if working_links:
        with open("vless_proxies.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(working_links))
            
        # Генерируем также готовую Base64 подписку прямо в репозитории
        raw_text = "\n".join(working_links)
        base64_sub = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write(base64_sub)
            
        print("💾 База успешно обновлена очищенными серверами!")

if __name__ == "__main__":
    main()
