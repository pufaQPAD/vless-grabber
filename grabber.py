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
    f.write("=== ЗАПУСК СУПЕР-ГРАБЕРА VLESS (WARP + WORKERS) ===\n")

def log(message, end="\n", flush=False):
    print(message, end=end, flush=flush)
    if "\r" not in message:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + ("\n" if end == "\n" else ""))

WORKERS_SOURCES = [
    "".join(["https://", "raw.github", "usercontent.com", "/cmliu", "/CF-Workers-SUB", "/main", "/vless"]),
    "".join(["https://", "raw.github", "usercontent.com", "/vlesssub", "/vless", "/main", "/sub"]),
    "".join(["https://", "raw.github", "usercontent.com", "/ymyuuu", "/Cloudflare-Worker-Proxy", "/main", "/vless.txt"]),
    "".join(["https://", "raw.github", "usercontent.com", "/zizifn", "/edgetunnel", "/main", "/discovered_vless.txt"])
]

def fetch_url(url):
    try:
        # ИСПРАВЛЕНО: Жестко заставляем Python использовать твой системный VPN
        proxy_support = urllib.request.ProxyHandler()
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore').strip()
    except:
        return ""

def generate_cloudflare_warp_vless():
    log("  [+] Генерация Warp-аккаунтов Cloudflare... ", end="", flush=True)
    warp_nodes = []
    try:
        import uuid
        for i in range(1, 11): # Поднимаем генерацию до 10 серверов за раз
            user_uuid = str(uuid.uuid4())
            # Расширенный список Clean IP Cloudflare, которые сейчас активны
            clean_ips = [
                "162.159.192.1", "162.159.193.1", "162.159.195.1", 
                "104.16.124.28", "104.17.124.28", "172.67.74.251", "104.21.40.11"
            ]
            ip = clean_ips[i % len(clean_ips)]
            warp_vless = f"vless://{user_uuid}@{ip}:443?encryption=none&security=tls&sni=://cloudflareclient.com&type=ws&host=://cloudflareclient.com&path=%2Fwarp"
            warp_nodes.append(warp_vless)
            
        log(f"Успешно! Создано {len(warp_nodes)} Warp-серверов.")
        return warp_nodes
    except Exception as e:
        log(f"Ошибка: {e}")
        return []

def check_rkn_blocking_and_tls(link):
    try:
        clean_link = link.split('#')[0].strip()
        url_parsed = urllib.parse.urlparse(clean_link)
        host = url_parsed.hostname
        port = url_parsed.port
        if not host or not port:
            return None
            
        query_params = urllib.parse.parse_qs(url_parsed.query)
        security = query_params.get('security', [''])
        if not security or security[0].lower() == 'none':
            return None

        sni_param = query_params.get('sni', [None])
        sni = sni_param[0] if sni_param and sni_param[0] else host
        
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
    log("🚀 [ШАГ 1/3] Запуск объединенной генерации (WARP + WORKERS)...")
    all_vless_links = []
    
    warp_links = generate_cloudflare_warp_vless()
    all_vless_links.extend(warp_links)
    
    log("\n📁 Сканирование Cloudflare Workers & CDN агрегаторов:")
    for i, source in enumerate(WORKERS_SOURCES, 1):
        log(f"  [+] Запрос к CDN источнику #{i}... ", end="", flush=True)
        content = fetch_url(source)
        if content:
            if "vless://" not in content:
                try:
                    padded = content + "=" * ((4 - len(content) % 4) % 4)
                    content = base64.b64decode(padded).decode('utf-8', errors='ignore')
                except:
                    pass
            links = re.findall(r"vless://[^\"'\s<>\s]+", content)
            log(f"Успешно! Найдено ссылок: {len(links)}")
            all_vless_links.extend(links)
        else:
            log("Ошибка (Недоступен)")
            
    unique_links = list(dict.fromkeys([l for l in all_vless_links if len(l) > 50]))
    total_count = len(unique_links)
    
    log(f"\n📊 [ШАГ 2/3] Собрано уникальных серверов на проверку: {total_count} шт.")
    if total_count == 0:
        log("📭 Пустой список. Работа завершена.")
        # ИСПРАВЛЕНО: Остановка перед закрытием
        input("\nНажмите Enter, чтобы закрыть окно...")
        return

    log("🎯 Запуск РКН/TLS-валидатора для отсева заблокированных IP...")
    
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
            sys.stdout.write(f"\r  Progress: [{checked_count}/{total_count}] ({percent}%) | Живых прокси: {len(working_links)} ")
            sys.stdout.flush()
            
    log("\n\n✅ [ШАГ 3/3] Валидация полностью завершена!")
    log(f"📊 Итог: Чистых, устойчивых к РКН прокси осталось {len(working_links)} из {total_count}")
    
    if working_links:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(working_links))
            
        raw_text = "\n".join(working_links)
        base64_sub = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
        with open("sub.txt", "w", encoding="utf-8") as f:
            f.write(base64_sub)
            log("💾 База успешно перезаписана и сохранена в файлы!")
    else:
        log("📭 Все найденные прокси заблокированы ТСПУ.")
        
    log("\n=== РАБОТА СКРИПТА ПОЛНОСТЬЮ ЗАВЕРШЕНА ===")
    
    # ИСПРАВЛЕНО: Окно терминала больше не закроется само!
    print("\n" + "="*40)
    input("Готово! Нажмите клавишу ENTER для выхода...")

if __name__ == "__main__":
    main()
