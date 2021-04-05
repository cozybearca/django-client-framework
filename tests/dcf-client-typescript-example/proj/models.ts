import {
    Model,
    CollectionManager,
    RelatedObjectManager,
    RelatedCollectionManager,
} from "django-client-framework"

class Product extends Model {
    static readonly objects = new CollectionManager(Product)
    get brand() {
        return new RelatedObjectManager(Brand, this, "brand")
    }
    id: number = 0
    barcode: string = ""
    brand_id?: number
}

class Brand extends Model {
    static readonly objects = new CollectionManager(Brand)
    get products() {
        return new RelatedCollectionManager(Product, this, "products")
    }
    id: number = 0
    name: string = ""
}

export { Product, Brand }
