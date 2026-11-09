"""Выпуск QR для проверенной публичной страницы /app/."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class StoreLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ready = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href", "").startswith("https://"):
            self.ready.add(attrs.get("id"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Полный опубликованный адрес страницы /app/")
    args = parser.parse_args()
    address = urlsplit(args.url)
    if (address.scheme != "https" or not address.hostname or address.username
            or not address.path.rstrip("/").endswith("/app") or address.query or address.fragment):
        parser.error("Нужен HTTPS-адрес страницы /app/ без параметров и фрагмента.")

    local = Path(__file__).parent.joinpath("docs/app/index.html").read_bytes()
    stores = StoreLinks()
    stores.feed(local.decode("utf-8"))
    if "app-store" not in stores.ready or not stores.ready.intersection({"google-play", "rustore"}):
        parser.error("Сначала укажите адреса приложения для iOS и Android.")

    import segno

    request = Request(args.url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=20) as response:
        canonical = response.geturl()
        if (response.status != 200 or canonical.rstrip("/") != args.url.rstrip("/")
                or response.read(len(local) + 1) != local):
            parser.error("По этому адресу не удалось подтвердить публикацию текущей страницы.")

    qr = segno.make_qr(canonical, error="m")
    qr.save("app-qr.svg", scale=8, border=4, light="white")
    qr.save("app-qr.png", scale=16, border=4, light="white")
    print(f"{canonical}\nГотовы app-qr.svg и app-qr.png")


if __name__ == "__main__":
    main()
