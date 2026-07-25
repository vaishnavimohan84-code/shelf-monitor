# Route Reference

All routes require login (`@login_required`) unless noted. Routes under
`/users` (except `/users/change-password`) additionally require the
`admin` role.

## Auth (`/auth`)
| Method | Path | Description |
|---|---|---|
| GET/POST | `/auth/login` | Login form / authenticate |
| GET | `/auth/logout` | Log out current user |

## Dashboard (`/dashboard`)
| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/` | KPIs + Chart.js analytics (scans/day, alert breakdown, top shelves) |

## Products (`/products`)
| Method | Path | Description |
|---|---|---|
| GET | `/products/` | List, search (`?q=`), filter by category (`?category=`) |
| GET/POST | `/products/new` | Create product (with image upload) |
| GET/POST | `/products/<id>/edit` | Edit product |
| POST | `/products/<id>/delete` | Delete product |

## Shelves (`/shelves`)
| Method | Path | Description |
|---|---|---|
| GET | `/shelves/` | List, search (`?q=`) |
| GET/POST | `/shelves/new` | Create shelf |
| GET/POST | `/shelves/<id>/edit` | Edit shelf |
| POST | `/shelves/<id>/delete` | Delete shelf |
| GET/POST | `/shelves/<id>/planogram` | View/add planogram entries |
| POST | `/shelves/<id>/planogram/<entry_id>/remove` | Remove a planogram entry |

## Detection (`/detection`)
| Method | Path | Description |
|---|---|---|
| GET/POST | `/detection/upload` | Upload a shelf image and run YOLOv8 |
| GET/POST | `/detection/webcam` | Capture a webcam frame and run YOLOv8 |
| GET | `/detection/result/<log_id>` | View annotated result + counts for one scan |
| GET | `/detection/history` | List past scans, filter by shelf (`?shelf_id=`) |

## Reports (`/reports`)
| Method | Path | Description |
|---|---|---|
| GET | `/reports/` | Report generation form |
| POST | `/reports/generate` | Generate a report (`format=pdf\|excel\|csv`, optional `start_date`, `end_date`, `shelf_id`) |
| GET | `/reports/download/<filename>` | Download a generated report file |

## Users (`/users`) — admin only unless noted
| Method | Path | Description |
|---|---|---|
| GET | `/users/` | List users |
| GET/POST | `/users/new` | Create user |
| GET/POST | `/users/<id>/edit` | Edit user |
| POST | `/users/<id>/toggle-active` | Activate/deactivate a user |
| POST | `/users/<id>/delete` | Delete a user |
| GET/POST | `/users/change-password` | *(any logged-in user)* change own password |

## CLI commands (`flask --app run.py <command>`)
| Command | Description |
|---|---|
| `init-db` | Create all tables from SQLAlchemy models (alternative to `schema.sql`) |
| `create-admin` | Interactively create an admin user |
