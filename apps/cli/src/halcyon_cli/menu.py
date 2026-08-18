"""Terminal front-end for the internal product control API.

This module only collects input and prints results; every HTTP call is delegated
to `api_client`, the same module the web server uses.
"""

from pprint import pprint

from . import api_client

OPTIONS = [
    "1. List registered items",
    "2. Find item by name",
    "3. Register item",
    "4. Update item - all fields (PUT)",
    "5. Update item - only some fields (PATCH)",
    "6. Remove item",
    "7. Exit",
]


def ask_text(prompt, required=True):
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("  This field cannot be empty.")


def ask_float(prompt, minimum=None, maximum=None):
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("  Please type a number, e.g. 349.90")
            continue
        if minimum is not None and value < minimum:
            print(f"  Value must be at least {minimum}.")
            continue
        if maximum is not None and value > maximum:
            print(f"  Value must be at most {maximum}.")
            continue
        return value


def ask_int(prompt, minimum=None):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("  Please type a whole number, e.g. 42")
            continue
        if minimum is not None and value < minimum:
            print(f"  Value must be at least {minimum}.")
            continue
        return value


def ask_bool(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer with y or n.")


def ask_tags(prompt):
    raw = input(prompt).strip()
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def ask_product_fields(new=True):
    """Collect the full item body required by POST and PUT."""
    label = "" if new else "new "
    return {
        "name": ask_text(f"Enter {label}item name: "),
        "category": ask_text(f"Enter {label}item category: "),
        "price": ask_float(f"Enter {label}unit cost: ", minimum=0),
        "stock": ask_int(f"Enter {label}quantity on hand: ", minimum=0),
        "in_stock": ask_bool("Is the line in service? (n withdraws it, whatever the quantity) (y/n): "),
        "rating": ask_float(f"Enter {label}quality rating (0-5): ", minimum=0, maximum=5),
        "tags": ask_tags(f"Enter {label}item tags (comma-separated): "),
    }


def ask_patch_fields():
    """Collect only the fields the user wants to change - that is what PATCH is for."""
    fields = {}
    if ask_bool("Change the name? (y/n): "):
        fields["name"] = ask_text("Enter new item name: ")
    if ask_bool("Change the category? (y/n): "):
        fields["category"] = ask_text("Enter new item category: ")
    if ask_bool("Change the unit cost? (y/n): "):
        fields["price"] = ask_float("Enter new unit cost: ", minimum=0)
    if ask_bool("Change the quantity on hand? (y/n): "):
        fields["stock"] = ask_int("Enter new quantity on hand: ", minimum=0)
    if ask_bool("Withdraw or return the line to service? (y/n): "):
        fields["in_stock"] = ask_bool("Is the line in service? (n withdraws it, whatever the quantity) (y/n): ")
    if ask_bool("Change the quality rating? (y/n): "):
        fields["rating"] = ask_float("Enter new quality rating (0-5): ", minimum=0, maximum=5)
    if ask_bool("Change the tags? (y/n): "):
        fields["tags"] = ask_tags("Enter new item tags (comma-separated): ")
    return fields


def show(result, success_title):
    """Print an api_client result using the shared success/error shape."""
    if not result["success"]:
        print(f"\n{result['message']}")
        if result["detail"]:
            print(f"Detail: {result['detail']}")
        return

    print(f"\n{success_title}")
    data = result["data"]
    if isinstance(data, list):
        for item in data:
            pprint(item)
    else:
        pprint(data)


def menu():
    while True:
        print("\nMenu:")
        for option in OPTIONS:
            print(option)
        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            show(api_client.list_products(), "Registered items:")
        elif choice == "2":
            name = ask_text("Enter item name to search: ")
            show(api_client.get_products_by_name(name), "Search result:")
        elif choice == "3":
            fields = ask_product_fields(new=True)
            show(api_client.create_product(fields["name"], fields), "Item registered:")
        elif choice == "4":
            name = ask_text("Enter item name to update: ")
            fields = ask_product_fields(new=False)
            show(api_client.replace_product(name, fields), "Item updated:")
        elif choice == "5":
            name = ask_text("Enter item name to update: ")
            fields = ask_patch_fields()
            if not fields:
                print("\nNothing to change - no fields selected.")
                continue
            show(api_client.update_product_fields(name, fields), "Item partially updated:")
        elif choice == "6":
            name = ask_text("Enter item name to remove: ")
            show(api_client.delete_product(name), "Item removed:")
        elif choice == "7":
            print("Exiting...")
            return
        else:
            print("Invalid option. Please try again.")
