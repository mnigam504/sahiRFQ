"""Local-only demo server; intentionally not a production hosting stack."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .engine import Engine
from .qa import answer
from .quotes import compare

ROOT=Path(__file__).resolve().parents[1]


def make_handler(engine):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,format,*args):
            # Requests are not logged: buyer text could contain sensitive information.
            pass

        def send(self,status,content,ctype='application/json; charset=utf-8'):
            body=content if isinstance(content,bytes) else json.dumps(content,ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path=urlsplit(self.path).path
            if path=='/api/health':
                return self.send(200,{'status':'ok','records':len(engine.catalog),'training_records':engine.router.training_count,
                                      'catalog_fingerprint':engine.index.fingerprint,'llm_configured':bool(__import__('os').environ.get('OPENAI_API_KEY') and __import__('os').environ.get('OPENAI_MODEL'))})
            if path=='/api/policies': return self.send(200,engine.policies)
            if path=='/api/evaluation':
                report=ROOT/'reports'/'evaluation.json'
                return self.send(200,json.loads(report.read_text()) if report.exists() else {'note':'Run python scripts/evaluate.py.'})
            # Static allowlist avoids arbitrary file reads and symlink/path traversal.
            paths={'/':'index.html','/style.css':'style.css','/app.js':'app.js'}
            if path not in paths: return self.send(404,{'error':'Not found'})
            f=ROOT/'web'/paths[path]
            return self.send(200,f.read_bytes(),mimetypes.guess_type(f.name)[0]+'; charset=utf-8')

        def do_POST(self):
            # No cross-origin mutations/API-key use from third-party webpages.
            origin=self.headers.get('Origin')
            host=self.headers.get('Host','')
            if origin and origin not in {f'http://{host}',f'https://{host}'}:
                return self.send(403,{'error':'Cross-origin requests are disabled.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.send(415,{'error':'Use application/json.'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=32000: return self.send(413,{'error':'Invalid or oversized request.'})
                obj=json.loads(self.rfile.read(length))
                if not isinstance(obj,dict): raise ValueError('Request body must be a JSON object.')
                path=urlsplit(self.path).path
                if path=='/api/analyze':
                    result=engine.analyze(obj.get('text'),obj.get('answers'))
                    result['rfq_draft']=engine.export_rfq(result)
                    return self.send(200,result)
                if path=='/api/ask':
                    if not isinstance(obj.get('use_llm',False),bool): raise ValueError('use_llm must be a boolean.')
                    return self.send(200,answer(engine,obj.get('question'),obj.get('record_ids'),obj.get('use_llm',False)))
                if path=='/api/quotes':
                    return self.send(200,compare(engine,obj.get('text'),obj.get('answers'),obj.get('quotes')))
                return self.send(404,{'error':'Not found'})
            except (ValueError,TypeError) as exc:
                return self.send(400,{'error':str(exc)})
            except Exception:
                return self.send(500,{'error':'Internal demo error. Check the request and restart the server.'})
    return Handler


def main():
    parser=argparse.ArgumentParser(description='Run the SahiRFQ local ML demo.')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    engine=Engine()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(engine))
    print(f'SahiRFQ: http://127.0.0.1:{args.port} (local-only; Ctrl+C to stop)',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
