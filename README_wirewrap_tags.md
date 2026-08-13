# Wire-Wrap Tag Toolset v6

Changes in v6:

- Pin numbers remain inside the two pin rows.
- The part ID remains rotated top-to-bottom.
- The part ID is now shifted **0.925 mm to the left** by default, roughly half of the default ID text height.
- This clears the high-number/right-side pin-number column.
- The horizontal offset is now parameterized with `--id-x-offset`.

Example:

```bash
python3 wirewrap_labels.py --pins 16 --width 300 --id IC12 -o IC12.svg
```

Adjust the ID farther left:

```bash
python3 wirewrap_labels.py --pins 16 --width 300 --id IC12 --id-x-offset -1.2 -o IC12.svg
```

Move it back toward center:

```bash
python3 wirewrap_labels.py --pins 16 --width 300 --id IC12 --id-x-offset -0.5 -o IC12.svg
```

The ID size is also adjustable:

```bash
python3 wirewrap_labels.py --pins 16 --width 300 --id IC12 --id-size 1.6 -o IC12.svg
```

Print labels at 100% / Actual Size with scaling disabled.
