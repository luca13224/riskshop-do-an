from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    sku: str
    slug: str
    name: str
    category: str
    category_name: str
    description: str
    price: int
    image_url: str | None
    stock: int

    model_config = {"from_attributes": True}


class ProductPage(BaseModel):
    """Một trang kết quả: danh sách + thông tin phân trang."""

    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class CategoryOut(BaseModel):
    code: str
    name: str
    product_count: int
