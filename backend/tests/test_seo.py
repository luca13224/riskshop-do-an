"""Test robots.txt và sitemap.xml (SEO)."""

import xml.etree.ElementTree as ET

from app.modules.catalog.models import Product

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def test_robots_blocks_private_areas_and_points_to_sitemap(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    for path in ("/console", "/checkout", "/orders", "/api/"):
        assert f"Disallow: {path}" in r.text
    assert "Sitemap: " in r.text and r.text.rstrip().endswith("/sitemap.xml")


def test_sitemap_lists_only_public_active_pages(client, db):
    db.add_all([
        Product(sku="S-1", slug="tai-nghe-a", name="Tai nghe A", category="audio", price=500_000, stock=5),
        Product(sku="S-2", slug="hang-an", name="Hàng ẩn", category="gear", price=100_000, stock=1, is_active=False),
    ])
    db.commit()

    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    locs = [e.text for e in ET.fromstring(r.content).findall("s:url/s:loc", NS)]
    assert any(loc.endswith("/products/tai-nghe-a") for loc in locs)
    assert not any("hang-an" in loc for loc in locs)  # sản phẩm ngừng bán không vào sitemap
    assert any(loc.endswith("/danh-muc/audio") for loc in locs)
    assert not any("/danh-muc/gear" in loc for loc in locs)  # danh mục không còn hàng thì bỏ qua
    assert not any("/console" in loc or "/orders" in loc for loc in locs)
