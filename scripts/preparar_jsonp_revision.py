"""Build deterministic script companions for a static review host's opaque origin.

Original JSON/GeoJSON bytes and published SHA-256 stay unchanged. Companions carry
the original UTF-8 text as an ASCII-escaped JavaScript string. No ETL or downloads.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'lakehouse/sitio'
MARKER = '// Static review JSON transport; generated from unchanged source bytes.\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    sources=sorted(p for p in SITE.rglob('*') if p.is_file() and p.suffix.lower() in {'.json','.geojson'})
    before={p:sha256(p.read_bytes()).hexdigest() for p in sources}
    entries=[]
    for path in sources:
        raw=path.read_bytes()
        text=raw.decode('utf-8')
        assert text.encode('utf-8')==raw
        json.loads(text.lstrip('\ufeff'))
        relative=path.relative_to(SITE).as_posix()
        wrapper=(MARKER+'window.__reviewJsonpLoad__('+json.dumps(relative,ensure_ascii=True)+','
                 +json.dumps(text,ensure_ascii=True)+');\n').encode('ascii')
        assert len(wrapper)<8_000_000, (relative,len(wrapper))
        companion=Path(str(path)+'.jsonp.js')
        if companion.exists():
            assert companion.read_bytes().startswith(MARKER.encode('ascii')), companion
        companion.write_bytes(wrapper)
        entries.append({'source':relative,'source_bytes':len(raw),'source_sha256_before':before[path],
                        'source_sha256_after':sha256(path.read_bytes()).hexdigest(),
                        'companion':companion.relative_to(SITE).as_posix(),'companion_bytes':len(wrapper),
                        'companion_sha256':sha256(wrapper).hexdigest(),'original_text_round_trip':True})
    assert all(before[p]==sha256(p.read_bytes()).hexdigest() for p in sources)
    report={'status':'pass','source_files':len(entries),'original_sources_unchanged':True,
            'all_companions_under_8_MB':True,'largest_companion':max(entries,key=lambda x:x['companion_bytes']),
            'total_original_bytes':sum(x['source_bytes'] for x in entries),
            'total_companion_bytes':sum(x['companion_bytes'] for x in entries),
            'transport':'Classic scripts allowed by existing CSP; no CORS/header/security changes.',
            'entries':entries}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
