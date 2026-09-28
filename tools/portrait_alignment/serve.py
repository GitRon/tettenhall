"""
Serve the portrait alignment page on http://127.0.0.1:8765/ and write what it places into the fixture.

    python tools/portrait_alignment/serve.py

Standard library only. The page reads the layers cut by cut_sheet.py from static/img/warrior/portrait/,
and the offsets of every hair and beard piece live in apps/warband/fixtures/portraitpiece.json - the
page edits that file in place, so there is no second copy to keep in step. Run "loaddata portraitpiece"
afterwards to see a change in the game.
"""

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PORTRAIT = ROOT / "static" / "img" / "warrior" / "portrait"
FIXTURE = ROOT / "apps" / "warband" / "fixtures" / "portraitpiece.json"
FACE_SIZE = (198, 204)
PORT = 8765


def read_placement() -> dict:
    """
    The fixture's hair and beard rows in the shape the page edits: keyed by kind and number.
    """
    placement = {"canvas": {"width": FACE_SIZE[0], "height": FACE_SIZE[1]}, "hair": {}, "beard": {}}
    for row in json.loads(FIXTURE.read_text(encoding="utf-8")):
        fields = row["fields"]
        if fields["kind"] in ("hair", "beard"):
            placement[fields["kind"]][f"{fields['number']:02d}"] = {
                "left": fields["left"],
                "top": fields["top"],
                "width": fields["width"],
                "placed": True,
            }
    return placement


def write_placement(*, placement: dict) -> None:
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for row in rows:
        fields = row["fields"]
        piece = placement.get(fields["kind"], {}).get(f"{fields['number']:02d}")
        if piece:
            fields.update(left=piece["left"], top=piece["top"], width=piece["width"])
    with FIXTURE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:  # noqa: PBR001 - the signature http.server calls
        path = path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return str(HERE / "index.html")
        if path == "/pieces.json":
            return str(HERE / "pieces.json")
        if path.startswith("/portrait/"):
            return str(PORTRAIT / path.removeprefix("/portrait/"))
        return str(HERE / "__missing__")

    def do_GET(self) -> None:
        if self.path.startswith("/placement.json"):
            self._send_json(status=200, payload=read_placement())
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/placement.json":
            self._send_json(status=404, payload={"error": "not found"})
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            placement = json.loads(body)
        except json.JSONDecodeError as error:
            self._send_json(status=400, payload={"error": str(error)})
            return
        write_placement(placement=placement)
        self._send_json(status=200, payload={"saved": str(FIXTURE)})

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send_json(self, *, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(HERE)))
    print(f"Portrait alignment on http://127.0.0.1:{PORT}/ - writing {FIXTURE}")
    server.serve_forever()
