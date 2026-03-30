#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 用法：python3 inject_data.py

import requests, csv, json, re, io
from datetime import datetime

SHEET_ID   = '1lNGJ9hGziZYXHfUNbLFSqkyZB0bUFa0APvZL1QDbuSA'
GID_BLANKS = '0'
GID_6012   = '57603327'
HTML_IN    = 'substrate_inventory.html'
HTML_OUT   = 'index.html'

def csv_url(gid):
    return (f'https://docs.google.com/spreadsheets/d/{SHEET_ID}'
            f'/gviz/tq?tqx=out:csv&gid={gid}')

def fetch_csv(gid):
    r = requests.get(csv_url(gid), timeout=15)
    r.raise_for_status()
    if r.text.strip().startswith('<'):
        raise ValueError('Google 回傳 HTML，請確認試算表已設定公開分享（知道連結的人可以檢視）')
    return list(csv.reader(io.StringIO(r.text)))

def find_col(headers, keys):
    h = [x.lower().strip() for x in headers]
    for k in keys:
        for i, v in enumerate(h):
            if k in v:
                return i
    return -1

def parse_blanks(rows):
    # 從標題列找各欄位的實際 index（用欄位名稱比對，不用固定數字）
    header = rows[0]
    def find(name):
        for i, v in enumerate(header):
            if v.strip() == name:
                return i
        return -1

    col_wh   = find('庫別')      # D欄
    col_car  = find('載具')      # E欄
    col_spec = find('規格')      # I欄
    col_lot  = find('Metal Lot') # J欄
    col_pur  = find('使用目的')  # N欄
    col_note = find('備註')      # O欄

    print(f'  欄位對應: 庫別={col_wh}, 載具={col_car}, 規格={col_spec}, Metal Lot={col_lot}, 使用目的={col_pur}, 備註={col_note}')

    result = []
    for row in rows[1:]:
        if len(row) <= max(col_wh, col_car, col_spec, col_lot, col_pur, col_note):
            continue
        wh = row[col_wh].strip() if col_wh >= 0 else ''
        if 'A倉' not in wh and 'B倉' not in wh:
            continue
        lot  = row[col_lot].strip()  if col_lot  >= 0 else ''
        spec = row[col_spec].strip() if col_spec >= 0 else ''
        if not lot and not spec:
            continue
        result.append({
            'lot':  lot,
            'spec': spec,
            'wh':   wh,
            'car':  row[col_car].strip()  if col_car  >= 0 else '',
            'pur':  row[col_pur].strip()  if col_pur  >= 0 else '',
            'note': row[col_note].strip() if col_note >= 0 else '',
        })
    return result

def parse_6012(rows):
    unused, scrap, h_idx = None, None, -1
    for i, row in enumerate(rows[:12]):
        joined = ' '.join(row)
        if re.search(r'未使用|available', joined, re.I):
            nums = [int(x) for x in re.findall(r'\d+', ''.join(row))]
            if nums: unused = nums[0]
        if re.search(r'報廢|scrap', joined, re.I):
            nums = [int(x) for x in re.findall(r'\d+', ''.join(row))]
            if nums: scrap = nums[0]
        if re.search(r'工號|時間|方式|employee|date|method', joined, re.I):
            h_idx = i
    if h_idx < 0: h_idx = 0
    hdr = rows[h_idx]
    C = {
        'emp':  find_col(hdr, ['工號','人員','employee']),
        'time': find_col(hdr, ['時間','日期','date','time']),
        'mth':  find_col(hdr, ['方式','method','type','操作']),
        'mch':  find_col(hdr, ['機台','machine']),
        'pat':  find_col(hdr, ['描畫','pattern']),
        'pm':   find_col(hdr, ['pm','pm項目']),
        'note': find_col(hdr, ['備註','note','remark']),
    }
    result = []
    for row in rows[h_idx+1:]:
        if not any(row): continue
        def g(k): return row[C[k]].strip() if C[k] >= 0 and C[k] < len(row) else ''
        result.append({'emp':g('emp'),'time':g('time'),'mth':g('mth'),
                       'mch':g('mch'),'pat':g('pat'),'pm':g('pm'),'note':g('note')})
    return unused, scrap, result

def inject(blanks, unused, scrap, rows_6012):
    generated = datetime.now().strftime('%Y/%m/%d %H:%M')
    static_data = {
        'generated': generated,
        'blanks': blanks,
        's6012': {'unused': unused, 'scrap': scrap, 'rows': rows_6012}
    }
    js = ('const STATIC_DATA = '
          + json.dumps(static_data, ensure_ascii=False, separators=(',',':'))
          + ';')
    with open(HTML_IN, encoding='utf-8') as f:
        html = f.read()
    pattern = r'// STATIC_DATA_START.*?// STATIC_DATA_END'
    replacement = f'// STATIC_DATA_START\n{js}\n// STATIC_DATA_END'
    new_html, n = re.subn(pattern, replacement, html, flags=re.DOTALL)
    if n == 0:
        raise ValueError('找不到注入點（STATIC_DATA_START），請確認 HTML 已完成修改')
    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return generated

if __name__ == '__main__':
    print('正在讀取 Google Sheets...')
    try:
        blanks = parse_blanks(fetch_csv(GID_BLANKS))
        print(f'✓ Blanks：{len(blanks)} 筆')
        print('  前 5 筆：')
        for i, b in enumerate(blanks[:5]):
            print(f'  [{i}] {b}')

        unused, scrap, log = parse_6012(fetch_csv(GID_6012))
        print(f'✓ 6012：{len(log)} 筆紀錄，未使用 {unused} 片，可報廢 {scrap} 片')

        generated = inject(blanks, unused, scrap, log)
        print(f'✓ 輸出：{HTML_OUT}')
        print(f'  資料時間：{generated}')

    except Exception as e:
        print(f'\n✗ 錯誤：{e}')
        import sys; sys.exit(1)
