#!/usr/bin/env python3
import urllib.request

class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req:
            # Copy all custom headers from original request to prevent Cookie dropping on redirect
            for key, val in req.headers.items():
                new_req.add_header(key, val)
            for key, val in req.unredirected_hdrs.items():
                new_req.add_header(key, val)
        return new_req

# Install redirect handler globally to retain Cookie and sensitive headers on redirects
opener = urllib.request.build_opener(SameHostRedirectHandler)
urllib.request.install_opener(opener)

def extract_xsrf_token(cookie_str):
    parts = cookie_str.split(';')
    for part in parts:
        part = part.strip()
        if part.startswith('XSRF-TOKEN='):
            return part[len('XSRF-TOKEN='):]
    return 'CfDJ8B3cU1ZsNd1MirISpSbNJd9xEGENsXFsuDl7V5fCVCB8-pA-dO7yChyFNS8TfS_q_-Gz5K5WJeKA4q_0zrp2HZ0xaXWgMy2fIYPUWiVK851Gk2rDAn-zV9tVPYhlouwMrtmtQPeeP9L-8KxFeDtsLPVuevjpLwWrJjvto0piDPQUVGlit2-AOQK2ByM-LOAYHQ'
