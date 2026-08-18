"""Fill the register with a catalogue of example products.

Run it from apps/api, like alembic, so the settings resolve the same .env and
the same HALCYON_DATABASE_URL the API itself will use:

    cd apps/api
    python seed.py            # insert whatever is missing
    python seed.py --reset    # empty the register first, then insert

The schema is Alembic's job: `alembic upgrade head` has to have run before
this. Nothing here creates a table, for the reason main.py gives - something
that quietly created what a migration should have made would let a database
drift away from the migration history without anyone noticing.

Products are matched by name, which is the unique column, so a name already
registered is left untouched and a second run inserts nothing.
"""

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import Engine, inspect, make_url
from sqlmodel import Session, select

from halcyon_api.config import get_settings
from halcyon_api.db import build_engine
from halcyon_api.models import Product, utcnow

# The prices, stock levels, ratings and tags below are generated rather than
# typed out, but from a fixed seed: two runs produce the same register, so a
# screenshot or a bug report stays reproducible.
SEED = 20260814

# Mirrors LOW_STOCK_THRESHOLD in apps/web/lib/stock.ts. It is duplicated on
# purpose - the seed has to know where the boundary is to place products on
# both sides of it, and the web client owns the rule for its own badges.
LOW_STOCK_THRESHOLD = 10

# Enough of each state that the dashboard tiles, the stock filter and all four
# badges have something to show.
#
# Out of stock and withdrawn are dealt separately because they are separate
# things: an empty shelf on a line still in service is a supply problem, while a
# withdrawn line is a decision, and most withdrawn lines still have units on the
# shelf. Collapsing them would leave the register unable to demonstrate the
# distinction the dashboard draws.
OUT_OF_STOCK = 9
WITHDRAWN = 5
LOW_STOCK = 18

# Mirrors STALE_COUNT_DAYS in apps/web/lib/stock.ts, for the same reason the
# low-stock threshold is duplicated: the seed has to know where the boundary is
# to place products on both sides of it.
STALE_COUNT_DAYS = 30

# A register that has been running for a while has a tail of quantities nobody
# has confirmed lately, and a few lines nobody has ever counted.
STALE_COUNTS = 14
NEVER_COUNTED = 3


@dataclass(frozen=True)
class CategorySpec:
    """A category's price band, the tags drawn from, and the products in it."""

    price_range: tuple[float, float]
    tags: tuple[str, ...]
    names: tuple[str, ...]


CATALOGUE: dict[str, CategorySpec] = {
    "Peripherals": CategorySpec(
        price_range=(12.0, 220.0),
        tags=("gaming", "compact", "hot-swappable", "wireless", "ergonomic", "office"),
        names=(
            "Mechanical Keyboard 60%",
            "Wireless Ergonomic Mouse",
            "Vertical Mouse Pro",
            "Numeric Keypad Slim",
            "Desk Mat XL",
            "Wrist Rest Memory Foam",
            "Keycap Set PBT",
            "USB Trackball",
            "Gaming Mousepad RGB",
            "Silent Mouse Bluetooth",
            "Low-Profile Keyboard",
            "Foot Pedal Controller",
            "Keyboard Wrist Guard",
            "Palm Rest Walnut",
        ),
    ),
    "Audio": CategorySpec(
        price_range=(18.0, 480.0),
        tags=("studio", "noise-cancelling", "usb-c", "streaming", "portable", "podcast"),
        names=(
            "Studio Headphones 250 Ohm",
            "Noise-Cancelling Earbuds",
            "USB Condenser Microphone",
            "Desktop Speaker Pair",
            "Boom Arm Stand",
            "Pop Filter Dual Layer",
            "Portable DAC Amp",
            "Bone-Conduction Headset",
            "Lavalier Microphone",
            "Audio Interface 2ch",
            "Shock Mount Universal",
            "Bluetooth Receiver",
            "Headphone Stand Aluminium",
        ),
    ),
    "Displays": CategorySpec(
        price_range=(25.0, 900.0),
        tags=("4k", "high-refresh", "colour-accurate", "vesa", "portable", "office"),
        names=(
            'Monitor 27" 4K IPS',
            'Monitor 24" 144Hz',
            'Ultrawide 34" Curved',
            'Portable Monitor 15.6"',
            "Monitor Arm Single",
            "Monitor Arm Dual",
            'Privacy Filter 24"',
            "Screen Light Bar",
            "Colour Calibrator",
            "Anti-Glare Sleeve",
            "VESA Adapter Plate",
            "Monitor Riser Bamboo",
        ),
    ),
    "Storage": CategorySpec(
        price_range=(14.0, 340.0),
        tags=("nvme", "portable", "backup", "high-endurance", "usb-c", "nas"),
        names=(
            "NVMe SSD 1TB",
            "NVMe SSD 2TB",
            "External SSD 500GB",
            "Portable HDD 4TB",
            "MicroSD Card 256GB",
            "SD Card V90 128GB",
            "NAS Drive 8TB",
            "USB Flash Drive 128GB",
            "SSD Enclosure USB-C",
            "Drive Dock Dual Bay",
            "M.2 Heatsink Kit",
            "Optical Drive External",
        ),
    ),
    "Networking": CategorySpec(
        price_range=(9.0, 400.0),
        tags=("wi-fi-7", "mesh", "gigabit", "poe", "rack", "shielded"),
        names=(
            "Wi-Fi 7 Router",
            "Mesh Node Pack",
            "Gigabit Switch 8-Port",
            "USB-C Ethernet Adapter",
            "Powerline Adapter Kit",
            "Network Cable Cat6 3m",
            "Patch Panel 12-Port",
            "PoE Injector",
            "Range Extender Dual-Band",
            "Fibre Media Converter",
            "Cable Tester RJ45",
            "Rack Shelf 1U",
        ),
    ),
    "Power": CategorySpec(
        price_range=(8.0, 260.0),
        tags=("gan", "fast-charge", "surge-protected", "usb-c", "travel", "braided"),
        names=(
            "Surge Protector 8-Way",
            "UPS 1500VA",
            "USB-C Charger 100W",
            "Power Bank 20000mAh",
            "GaN Charger 65W",
            "Cable USB-C 2m Braided",
            "Wireless Charging Pad",
            "Car Charger Dual",
            "Extension Reel 5m",
            "Battery AA Rechargeable",
            "Charging Station 6-Port",
            "Laptop Power Adapter 90W",
        ),
    ),
    "Workspace": CategorySpec(
        price_range=(11.0, 300.0),
        tags=("ergonomic", "adjustable", "bamboo", "cable-management", "office", "compact"),
        names=(
            "Standing Desk Frame",
            "Desk Lamp LED Dimmable",
            "Laptop Stand Aluminium",
            "Cable Management Tray",
            "Chair Lumbar Cushion",
            "Footrest Adjustable",
            "Drawer Organiser",
            "Whiteboard A2",
            "Desk Shelf Riser",
            "Anti-Fatigue Mat",
            "Cable Clips Pack",
            "Headset Hook Under-Desk",
            "Monitor Cleaning Kit",
        ),
    ),
    "Components": CategorySpec(
        price_range=(16.0, 1200.0),
        tags=("atx", "overclocking", "silent", "rgb", "ddr5", "80-plus-gold"),
        names=(
            "Graphics Card 12GB",
            "CPU Cooler Tower",
            "Case Fan 120mm Trio",
            "Thermal Paste 4g",
            "RAM Kit 32GB DDR5",
            "Motherboard ATX B650",
            "PSU 750W Gold",
            "PC Case Mid-Tower",
            "Fan Controller Hub",
            "Dust Filter Magnetic",
            "Riser Cable PCIe 4.0",
            "SATA Cable Pack",
        ),
    ),
}


def build_products() -> list[Product]:
    """The full catalogue, with generated numbers, ready to be inserted."""
    rng = random.Random(SEED)

    entries = [(category, name) for category, spec in CATALOGUE.items() for name in spec.names]

    # The states are dealt from a fixed pool rather than rolled per product, so
    # the counts are exact instead of merely likely.
    states = ["out"] * OUT_OF_STOCK + ["withdrawn"] * WITHDRAWN + ["low"] * LOW_STOCK
    states += ["in"] * (len(entries) - len(states))
    rng.shuffle(states)

    # Count freshness is dealt from its own pool, because it is an independent
    # axis: a stale figure can sit on any of the four states, and an item being
    # out of stock says nothing about when anyone last checked.
    freshness = ["stale"] * STALE_COUNTS + [None] * NEVER_COUNTED
    freshness += ["fresh"] * (len(entries) - len(freshness))
    rng.shuffle(freshness)

    now = utcnow()
    products: list[Product] = []

    for (category, name), state, age in zip(entries, states, freshness, strict=True):
        spec = CATALOGUE[category]
        stock, in_stock = _stock_for(state, rng)

        # Spread over the last year and a half, so the register reads like one
        # that grew rather than one written in a single second. A line dealt a
        # stale count is given an age to match: a quantity cannot have been
        # established before the item it describes existed, and clamping the
        # count date afterwards would make the pooled totals inexact.
        oldest = STALE_COUNT_DAYS + 1 if age == "stale" else 0
        created_at = now - timedelta(days=rng.randint(oldest, 540), minutes=rng.randint(0, 1440))

        products.append(
            Product(
                name=name,
                category=category,
                price=round(rng.uniform(*spec.price_range), 2),
                stock=stock,
                in_stock=in_stock,
                # Skewed towards the top: a catalogue is curated, so a flat
                # spread across 0-5 would look nothing like a real one.
                rating=round(rng.triangular(2.5, 5.0, 4.4), 1),
                tags=sorted(rng.sample(spec.tags, rng.randint(1, 3))),
                created_at=created_at,
                updated_at=min(now, created_at + timedelta(days=rng.randint(0, 45))),
                stock_counted_at=_counted_at(age, now, created_at, rng),
            )
        )

    return products


def _stock_for(state: str, rng: random.Random) -> tuple[int, bool]:
    """Quantity and availability for one of the four states the dashboard shows."""
    if state == "out":
        # An empty shelf on a line still in service: something to reorder.
        return 0, True

    if state == "withdrawn":
        # Taken out of service with units still on the shelf - the case a
        # `stock == 0` check alone would miss entirely, and the reason the
        # dashboard shows this apart from an empty shelf.
        return rng.randint(5, 60), False

    if state == "low":
        return rng.randint(1, LOW_STOCK_THRESHOLD), True

    return rng.randint(LOW_STOCK_THRESHOLD + 1, 400), True


def _counted_at(
    age: str | None,
    now: datetime,
    created_at: datetime,
    rng: random.Random,
) -> datetime | None:
    """When the quantity was last established, or None for one nobody has counted."""
    if age is None:
        return None

    if age == "stale":
        # Old enough to be flagged, but never older than the item itself.
        days = min(rng.randint(STALE_COUNT_DAYS + 1, 300), (now - created_at).days)
        return now - timedelta(days=max(days, 1))

    return now - timedelta(days=rng.randint(0, STALE_COUNT_DAYS - 1), minutes=rng.randint(0, 1440))


def require_schema(engine: Engine) -> None:
    """Stop with an instruction rather than a driver error on an unmigrated database."""
    if inspect(engine).has_table(Product.__tablename__):
        return

    raise SystemExit(
        f"The '{Product.__tablename__}' table does not exist yet.\n"
        "Create the schema first, from this directory:\n\n"
        "    alembic upgrade head\n"
    )


def clear(session: Session) -> int:
    """Remove every product, returning how many there were."""
    stored = session.exec(select(Product)).all()
    for product in stored:
        session.delete(product)

    session.commit()
    return len(stored)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load example products into the register.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete every product before inserting - the whole register, not just the seeded rows",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    engine = build_engine(settings)

    # hide_password, because a Postgres URL carries the credential and this
    # line ends up in terminals and CI logs.
    where = make_url(settings.database_url).render_as_string(hide_password=True)
    print(f"Register: {where}")

    require_schema(engine)

    catalogue = build_products()

    with Session(engine) as session:
        if args.reset:
            print(f"Removed {clear(session)} existing product(s).")

        registered = set(session.exec(select(Product.name)).all())

        added = 0
        for product in catalogue:
            if product.name in registered:
                continue

            session.add(product)
            added += 1

        session.commit()

        total = len(session.exec(select(Product)).all())

    print(f"Added {added} product(s), skipped {len(catalogue) - added} already registered.")
    print(f"The register now holds {total} product(s) across {len(CATALOGUE)} categories.")


if __name__ == "__main__":
    main()
