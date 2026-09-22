# QuietWriter bundled writing fonts

QuietWriter is prepared to register the font binaries in these folders as application fonts.
The binary `.ttf` files are intentionally fetched from the pinned public Google Fonts distribution during packaging/development by running:

    py tools/fetch_bundled_fonts.py

The manifest `font_manifest.json` contains the exact upstream URLs. Each family directory contains its required SIL Open Font License 1.1 text and copyright notice. The application continues to work when a binary is absent; only that bundled family is then unavailable unless it is installed as a system font.
