# supermarket-expense-recorder

A project that is going to help me save time.

## Personalized item names

When the receipt contains an item name that has not been reviewed before, the
script opens a small dialog to ask for a personalized name. Enter the preferred
name to save it, or leave the field blank/close the dialog to keep the receipt
name. The choice is saved in `item_name_mappings.json` next to
`expense_tracker_main.py` and reused for future receipts. This file is plain
JSON, so mappings can also be edited manually, for example:

```json
{
  "MA. G. NAC.": "Maçã Gala"
}
```
