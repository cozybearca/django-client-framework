import { Ajax } from "django-client-framework"
import { Product } from "./models"

Ajax.url_prefix = "http://localhost:8000"

async function main() {
    let product = await Product.objects.get({ id: 1 })

    console.log(product)
    // Product { id: 1, barcode: 'xxyy', brand_id: 1 }

    let nike = await product.brand.get()

    console.log(nike)
}

main()
