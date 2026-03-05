import requests
import sys
import json

def is_delay_related(text):
    keywords = ['遅れ', '遅延', '見合わせ', '運休', '変更']
    return any(kw in text for kw in keywords)

def main():
    url = "https://trafficinfo.westjr.co.jp/api/v1/trafficinfo.json"
    print(f"Fetching status from {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    delay_found = False
    delay_details = []

    def recursive_search(obj):
        nonlocal delay_found
        if isinstance(obj, dict):
            # effectLines等の線名
            line_name = obj.get('lineName', '') or obj.get('name', '')
            if '神戸線' in line_name:
                # sectionsがあれば調べる
                for sec in obj.get('sections', []):
                    cond = sec.get('conditionName', '')
                    if cond and cond != '平常':
                        delay_found = True
                        delay_details.append(f"{line_name} ({sec.get('startStation', '')}〜{sec.get('endStation', '')}) : {cond}")
            
            # 各テキストフィールド(body, text)
            for key in ['body', 'text', 'title']:
                val = obj.get(key)
                if isinstance(val, str) and '神戸線' in val:
                    if is_delay_related(val):
                        delay_found = True
                        delay_details.append(val.replace('\n', ' '))
                        
            for k, v in obj.items():
                recursive_search(v)
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item)

    recursive_search(data)

    delay_details = list(set(delay_details))

    if delay_found:
        print(">>> DELAY_DETECTED <<<")
        for detail in delay_details:
             print(f"- {detail}")
        # GitHub Actionsで遅延を検知させるため、環境変数等に出力することも可能だが、
        # 今回は単純に `DELAY_DETECTED` を標準出力に出し、ymlでgrepする。
    else:
        print(">>> NO_DELAY <<<")

if __name__ == "__main__":
    main()
