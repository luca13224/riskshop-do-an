"""Test module catalog: danh sách, tìm kiếm, lọc, phân trang, chi tiết, danh mục."""

import pytest

from app.modules.catalog.models import Product
from app.modules.catalog.seed import slugify


@pytest.fixture
def products(db):
    items = [
        Product(sku="T-1", slug="tai-nghe-a", name="Tai nghe A", category="audio", price=500_000, stock=5),
        Product(sku="T-2", slug="loa-b", name="Loa B", category="audio", price=300_000, stock=0),
        Product(sku="T-3", slug="ban-phim-c", name="Bàn phím C", category="computer", price=900_000, stock=3,
                description="Bàn phím có 100% phím"),
        Product(sku="T-4", slug="an-di", name="Sản phẩm đã ẩn", category="home", price=100_000, stock=1,
                is_active=False),
    ]
    db.add_all(items)
    db.commit()
    return items


def test_list_only_active_products(client, products):
    body = client.get("/api/products").json()
    assert body["total"] == 3
    assert "Sản phẩm đã ẩn" not in [p["name"] for p in body["items"]]


def test_product_has_category_name(client, products):
    item = client.get("/api/products/tai-nghe-a").json()
    assert item["category_name"] == "Âm thanh"
    assert item["price"] == 500_000


def test_filter_by_category(client, products):
    body = client.get("/api/products", params={"category": "audio"}).json()
    assert {p["sku"] for p in body["items"]} == {"T-1", "T-2"}


def test_unknown_category_rejected(client, products):
    resp = client.get("/api/products", params={"category": "khong-co"})
    assert resp.status_code == 422


def test_search_case_insensitive_and_in_description(client, products):
    assert client.get("/api/products", params={"q": "TAI NGHE"}).json()["total"] == 1
    assert client.get("/api/products", params={"q": "100%"}).json()["total"] == 1


def test_search_percent_is_literal_not_wildcard(client, products):
    # Nếu % không được escape, "%" sẽ khớp mọi sản phẩm
    assert client.get("/api/products", params={"q": "%"}).json()["total"] == 1


def test_pagination(client, products):
    first = client.get("/api/products", params={"page_size": 2, "page": 1}).json()
    second = client.get("/api/products", params={"page_size": 2, "page": 2}).json()
    assert len(first["items"]) == 2 and len(second["items"]) == 1
    assert not {p["sku"] for p in first["items"]} & {p["sku"] for p in second["items"]}


def test_page_size_limit(client, products):
    assert client.get("/api/products", params={"page_size": 1000}).status_code == 422


def test_inactive_or_missing_product_is_404(client, products):
    for slug in ("an-di", "khong-ton-tai"):
        resp = client.get(f"/api/products/{slug}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_categories_count_active_only(client, products):
    cats = {c["code"]: c["product_count"] for c in client.get("/api/categories").json()}
    assert cats["audio"] == 2 and cats["computer"] == 1 and cats["home"] == 0


def test_slugify_vietnamese():
    assert slugify("Bình giữ nhiệt Lumi 500ml") == "binh-giu-nhiet-lumi-500ml"
    assert slugify("Đồng hồ thông minh") == "dong-ho-thong-minh"
