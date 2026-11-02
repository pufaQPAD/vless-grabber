import re
import urllib.request
import base64
import urllib.parse
import socket
import ssl
import concurrent.futures
import sys
import os
import time

LOG_FILE = "grabber_log.txt"
OUTPUT_FILE = "vless_proxies.txt"

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("=== ЗАПУСК СОРТИРУЮЩЕГО ГРАБЕРА VLESS ===\n")

def log(message, end="\n", flush=False):
    print(message, end=end, flush=flush)
    if "\r" not in message:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + ("\n" if end == "\n" else ""))

SOURCES = [
    "".join(["https://", "raw.github", "usercontent.com", "/zu1k", "/proxys", "/main", "/proxies", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/vfarid", "/v2ray-share", "/main", "/exported", "/vpn.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/w1770946466", "/Auto_Proxy", "/main", "/v_links.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/tbbatbb", "/Proxy", "/main", "/v2ray", "/v2ray.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/mehrtat", "/vless-collector", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/yebekhe", "/TVC", "/main", "/protocols", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Fndroid", "/clash_config", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Bardiafa", "/Free-VLESS-VMess-SS", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/alien-v2ray", "/v2ray", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/cmliu", "/CF-Workers-SUB", "/main", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/vlesssub", "/vless", "/main", "/sub"]),
    "".join(["https://", "raw.github", "usercontent.com", "/ymyuuu", "/Cloudflare-Worker-Proxy", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/zizifn", "/edgetunnel", "/main", "/discovered_vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/Soroushx", "/v2ray-configs", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/barry-far", "/V2ray-Configs", "/main", "/All_Configs_Sub.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/officialputuid", "/Real-GUI-Sub", "/main", "/vless.txt"])
]

TELEGRAM_CHANNELS = [
    "v2ray_outline_vless_vmess", "FreeVlessVmessOutline", "vless_vmess_ss_shadowsocks",
    "nufilter", "V2Ray_Alpha", "v2rayNG_VPNo", "free_v2ray_config", "VlessConfig"
]

def fetch_url(url):
    try:
        proxy_support = urllib.request.ProxyHandler()
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read().decode('utf-8', errors='ignore').strip()
    except:
        return ""

def clean_html_tags(text):
    text = urllib.parse.unquote(text)
    return text.replace("&amp;", "&").replace("&#47;", "/").replace("%2F", "/").replace("&lt;", "<").replace("&gt;", ">").replace("&#58;", ":")

def decode_base64_if_needed(text):
    if "vless://" in text:
        return text
    try:
        padded_text = text + "=" * ((4 - len(text) % 4) % 4)
        return base64.b64decode(padded_text).decode('utf-8', errors='ignore')
    except:
        return text

def check_and_ping_tls(link):
    """Проверяет TLS порт и замеряет точную скорость отклика (пинг)"""
    try:
        clean_link = link.split('#')[0].strip()
        url_parsed = urllib.parse.urlparse(clean_link)
        host = url_parsed.hostname
        port = url_parsed.port if url_parsed.port else 443
        if not host:
            return None
            
        query_params = urllib.parse.parse_qs(url_parsed.query)
        sni_param = query_params.get('sni', [None])
        sni = sni_param[0] if sni_param and sni_param[0] else host
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.5)
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        secure_sock = context.wrap_socket(sock, server_hostname=sni)
        
        # ЗАМЕР СКОРОСТИ
        start_time = time.time()
        secure_sock.connect((host, int(port)))
        end_time = time.time()
        
        secure_sock.close()
        
        ping_ms = int((end_time - start_time) * 1000)
        return {"link": link, "ping": ping_ms}
    except:
        return None

def main():
    log("🚀 [ШАГ 1/3] Начинаем МАССОВЫЙ сбор прокси из всех источников...")
    all_vless_links = []
    
    log("\n📁 Сканирование репозиториев GitHub:")
    for i, source in enumerate(SOURCES, 1):
        log(f"  [+] Запрос к источнику GitHub #{i}... ", end="", flush=True)
        content = fetch_url(source)
        if content:
            cleaned = clean_html_tags(decode_base64_if_needed(content))
            links = re.findall(r"vless://[^\"'\s<>\s]+", cleaned)
            log(f"Успешно! Найдено ссылок: {len(links)}")
            all_vless_links.extend(links)
        else:
            log("Ошибка (Недоступен)")
            
    log("\n📢 Сканирование Telegram каналов:")
    for channel in TELEGRAM_CHANNELS:
        log(f"  [+] Чтение канала @{channel}... ", end="", flush=True)
        tg_url = f"https://t.me{channel}"
        html_content = fetch_url(tg_url)
        if not html_content or "vless://" not in html_content:
            slash = chr(47)
            html_content = fetch_url("".join(["https:", slash, slash, "telemetr.", "me", slash, "r", slash, channel]))
        if html_content:
            links = re.findall(r"vless://[^\"'\s<>\s]+", clean_html_tags(html_content))
            log(f"Успешно! Найдено ссылок: {len(links)}")
            all_vless_links.extend(links)
        else:
            log("Ошибка (Канал недоступен)")
            
    unique_links = list(dict.fromkeys([l for l in all_vless_links if len(l) > 50]))
    total_count = len(unique_links)
    
    log(f"\n📊 [ШАГ 2/3] Всего собрано уникальных прокси из сети: {total_count} шт.")
    if total_count == 0:
        log("📭 База пуста. Проверка отменена.")
        return

    log("🎯 Запуск измерителя скорости TLS для ранжирования пула...")
    
    checked_nodes = []
    checked_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_and_ping_tls, link): link for link in unique_links}
        for future in concurrent.futures.as_completed(futures):
            checked_count += 1
            res = future.result()
            if res:
                checked_nodes.append(res)
            
            percent = int((checked_count / total_count) * 100)
            sys.stdout.write(f"\r  Progress: [{checked_count}/{total_count}] ({percent}%) | Живых портов: {len(checked_nodes)} ")
            sys.stdout.flush()
            
    log("\n\n✅ [ШАГ 3/3] Замер задержек полностью завершен!")
    
    if checked_nodes:
        # СОРТИРОВКА: Сортируем список словарей по ключу 'ping' от меньшего к большему
        checked_nodes.sort(key=lambda x: x['ping'])
        
        # Вытаскиваем обратно чистые ссылки, которые теперь идут строго по качеству
        sorted_links = [node['link'] for node in checked_nodes]
        
        log(f"📊 Итог: Отсортировано лучших серверов: {len(sorted_links)} из {total_count}")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted_links))
            
        raw_text = "\n".join(sorted_links)
        base64_sub = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write(base64_sub)
        log("💾 База успешно отсортирована и сохранена!")
    else:
        log("📭 Ни один сервер не ответил.")
        
    log("\n=== РАБОТА СКРИПТА ПОЛНОСТЬЮ ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    main()
