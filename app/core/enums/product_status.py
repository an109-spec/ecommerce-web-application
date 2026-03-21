from enum import Enum

class ProductStatus(str, Enum):

    ACTIVE = "ACTIVE"            # user thấy
    DRAFT = "DRAFT"              # chỉ seller thấy / admin pending
    HIDDEN = "HIDDEN"            # tạm ẩn / admin rejected
    OUT_OF_STOCK = "OUT_OF_STOCK" # hết hàng
    DELETED = "DELETED"          # đã xóa