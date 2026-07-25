# Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DETECTION_LOGS : "creates"
    SHELVES ||--o{ DETECTION_LOGS : "scanned in"
    SHELVES ||--o{ SHELF_PRODUCTS : "has planogram"
    PRODUCTS ||--o{ SHELF_PRODUCTS : "expected on"
    DETECTION_LOGS ||--o{ DETECTION_ITEMS : "contains"
    PRODUCTS ||--o{ DETECTION_ITEMS : "matched to"
    SHELVES ||--o{ ALERTS : "raises"
    PRODUCTS ||--o{ ALERTS : "concerns"

    USERS {
        int id PK
        string username
        string email
        string password_hash
        enum role
        bool is_active_user
        datetime created_at
        datetime last_login
    }

    PRODUCTS {
        int id PK
        string name
        string sku
        string category
        string class_label
        int min_stock_threshold
        string image_path
    }

    SHELVES {
        int id PK
        string name
        string location
        string aisle
        text description
    }

    SHELF_PRODUCTS {
        int id PK
        int shelf_id FK
        int product_id FK
        int expected_quantity
    }

    DETECTION_LOGS {
        int id PK
        int shelf_id FK
        string source_image
        string annotated_image
        enum capture_type
        int total_products_detected
        float empty_shelf_percentage
        bool is_empty
        int created_by FK
        datetime created_at
    }

    DETECTION_ITEMS {
        int id PK
        int log_id FK
        int product_id FK
        string class_label
        float confidence
        int x1
        int y1
        int x2
        int y2
    }

    ALERTS {
        int id PK
        int shelf_id FK
        int product_id FK
        enum alert_type
        string message
        bool is_resolved
        datetime created_at
    }
```

## Relationship notes

- A **Shelf** has a planogram: a set of `SHELF_PRODUCTS` rows defining which
  products are expected on it and in what quantity.
- Every scan (image upload or webcam capture) creates one `DETECTION_LOGS`
  row and one `DETECTION_ITEMS` row per bounding box YOLOv8 finds.
- `DETECTION_ITEMS.product_id` is nullable because YOLOv8 may detect a class
  label that hasn't been registered as a `Product` yet.
- `ALERTS` are generated automatically by the detection pipeline
  (`app/utils/shelf_analysis.py`) for three cases: empty shelf, low stock,
  and misplaced product (a known product detected on a shelf where it isn't
  part of the planogram).
