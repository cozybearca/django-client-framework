import { Model, CollectionManager, Ajax } from "django-client-framework"

Ajax.url_prefix = "http://localhost:8000"

class Product extends Model {
    static readonly objects = new CollectionManager(Product)
    barcode: string = ""
}

async function main() {
    let page = await Product.objects.page({})
    console.log(page)
}

main()
