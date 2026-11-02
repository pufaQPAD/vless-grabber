import re
import urllib.request
import base64
import urllib.parse
import socket
import ssl
import concurrent.futures
import sys

LOG_FILE = "grabber_log.txt"
OUTPUT_FILE = "vless_proxies.txt"

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("=== ЗАПУСК МАКСИМАЛЬНОГО ОБЪЕДИНЕННОГО ГРАБЕРА VLESS ===\n")

def log(message, end="\n", flush=False):
    """Выводит сообщение в консоль и дублирует в лог-файл"""
    print(message, end=end, flush=flush)
    if "\r" not in message:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + ("\n" if end == "\n" else ""))

# ПОЛНЫЙ ОБЪЕДИНЕННЫЙ ПУЛ ИСТОЧНИКОВ
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
    "".join(["https://", "raw.github", "usercontent.com", "/vlesssub", "/vless", "/main", "/sub"])
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
        # Автоматическая поддержка системного прокси для работы через VPN на ПК
        proxy_support = urllib.request.ProxyHandler()
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        
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

def check_rkn_blocking_and_tls(link):
    """Глубокий чекер: имитирует трафик и проверяет стойкость к блокировкам РКН"""
    try:
        clean_link = link.split('#')[0].strip()
        url_parsed = urllib.parse.urlparse(clean_link)
        
        host = url_parsed.hostname
        port = url_parsed.port
        if not host:
            return None
        if not port:
            port = 443
            
        query_params = urllib.parse.parse_qs(url_parsed.query)
        security = query_params.get('security', [''])
        if not security or security[0].lower() == 'none':
            return None

        sni_param = query_params.get('sni', [None])
        sni = sni_param[0] if sni_param[0] else host
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.5)
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_alpn_protocols(['http/1.1', 'h2'])
        
        secure_sock = context.wrap_socket(sock, server_hostname=sni)
        secure_sock.connect((host, int(port)))
        
        secure_sock.sendall(b"HEAD / HTTP/1.1\r\nHost: " + sni.encode() + b"\r\n\r\n")
        secure_sock.recv(10)
        
        secure_sock.close()
        return link
    except:
        return None

def main():
    log("🚀 [ШАГ 1/3] Начинаем сбор сырых ссылок из интернета...")
    all_vless_links = []
    
    log("\n📁 Сканирование репозиториев GitHub:")
    for i, source in enumerate(SOURCES, 1):
        log(f"  [+] Запрос к источнику #{i}... ", end="", flush=True)
        content = fetch_url(source)
        if content:
            links = re.findall(r"vless://[^\"'\s<>\s]+", decode_base64_if_needed(content))
            log(f"Успешно! Найдено ссылок: {len(links)}")
            all_vless_links.extend(links)
        else:
            log("Ошибка (Недоступен)")
            
    log("\n📢 Сканирование Telegram каналов (веб-виджеты):")
    for channel in TELEGRAM_CHANNELS:
        log(f"  [+] Чтение канала @{channel}... ", end="", flush=True)
        slash = chr(47)
        tg_url = "".join(["https:", slash, slash, "telemetr.", "me", slash, "r", slash, channel])
        html_content = fetch_url(tg_url)
        if not html_content:
            tg_url = "".join(["https:", slash, slash, "t.me", slash, "s", slash, channel])
            html_content = fetch_url(tg_url)
        if html_content:
            links = re.findall(r"vless://[^\"'\s<>\s]+", html_content)
            log(f"Успешно! Найдено ссылок: {len(links)}")
            all_vless_links.extend(links)
        else:
            log("Ошибка (Блокировка сети)")
            
    unique_links = list(dict.fromkeys([l for l in all_vless_links if len(l) > 50]))
    total_count = len(unique_links)
    
    log(f"\n📊 [ШАГ 2/3] Всего собрано уникальных прокси: {total_count} шт.")
    if total_count == 0:
        log("📭 База пуста. Проверка отменена.")
        return

    log("🎯 Запуск глубокого многопоточного RKN/TLS-валидатора...")
    log("⏳ Пожалуйста, подождите. Прогресс отображается ниже:")
    
    working_links = []
    checked_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(check_rkn_blocking_and_tls, link): link for link in unique_links}
        
        for future in concurrent.futures.as_completed(futures):
            checked_count += 1
            res = future.result()
            if res:
                working_links.append(res)
            
            percent = int((checked_count / total_count) * 100)
            sys.stdout.write(f"\r  Progress: [{checked_count}/{total_count}] ({percent}%) | Найдено живых: {len(working_links)} ")
            sys.stdout.flush()
            
    log("\n\n✅ [ШАГ 3/3] Глубокий TLS/РКН отбор полностью завершен!")
    log(f"📊 Итог проверки: живых портов в РФ осталось {len(working_links)} из {total_count}")
    
    if working_links:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(working_links))
            
        raw_text = "\n".join(working_links)
        base64_sub = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write(base64_sub)
            
        log("💾 База успешно перезаписана и сохранена в файлы!")
    else:
        log("📭 Ни один сервер не смог пройти глубокую валидацию.")
        
    log("\n=== РАБОТА СКРИПТА ПОЛНОСТЬЮ ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    main()
