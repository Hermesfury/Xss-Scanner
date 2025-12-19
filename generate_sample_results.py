from types import SimpleNamespace
import xssscan

fake_results = [
    {
        "url": "http://127.0.0.1:8000/?search=test",
        "method": "GET",
        "params": ["search"],
        "payload": "<script>alert(1)</script>",
        "status": 200,
        "point_type": "url_param",
        "detection_method": "Reflected XSS",
        "bypasses": [],
        "snippet": "<div>you searched: <script>alert(1)</script></div>"
    }
]

args = SimpleNamespace(mode='reflected', stealth=False, aggressive_waf=False, geo_spoof=False, results_dir='test_results')

if __name__ == '__main__':
    xssscan.RESULTS_DIR = xssscan.Path(args.results_dir)
    xssscan.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    xssscan.save_results(fake_results, fake_results[0]['url'], args)
