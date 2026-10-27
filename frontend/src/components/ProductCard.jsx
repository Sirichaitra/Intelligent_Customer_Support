
import { Package, ExternalLink } from "lucide-react";

export default function ProductCard({ product = {} }) {
    if (!product || Object.keys(product).length === 0) {
        return null;
    }

    return (
        <div className="product-card">
            <div className="product-icon">
                <Package size={22} />
            </div>

            <div className="product-details">
                <h4>{product.name || product.title || "Related item"}</h4>

                {product.description && (
                    <p>{product.description}</p>
                )}

                {product.price != null && (
                    <p className="product-price">
                        Price: {product.price}
                    </p>
                )}

                {product.url && (
                    <a
                        href={product.url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        View details <ExternalLink size={14} />
                    </a>
                )}
            </div>
        </div>
    );
}
