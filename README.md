# MDrip 💧

<p align="center">
  <img src="assets/social_preview.png" alt="MDrip Social Preview" width="100%" />
</p>

> **A fast, aesthetic Windows desktop application that converts any file into clean Markdown — no Python or complex setup required.**

[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://github.com)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Engine: Microsoft MarkItDown](https://img.shields.io/badge/Powered%20By-Microsoft%20MarkItDown-5AD6C4)](https://github.com/microsoft/markitdown)

---

## 📖 About MDrip

**MDrip** is a modern desktop utility designed to effortlessly turn documents, spreadsheets, presentations, code files, and tabular data into clean, formatted Markdown (`.md`).

Built with a **frosted mint-aqua glass aesthetic** and retro **pixel-art accents**, MDrip combines visual elegance with high-performance engineering:
- **Instant startup** via background engine pre-warming.
- **Sub-millisecond conversions** via an intelligent fast-path parser.
- **Zero background overhead** via adaptive animation throttling.

Whether you're migrating docs into Obsidian, feeding documents into LLMs, or taking notes in Notion, MDrip makes file extraction as simple as drag-and-drop.

---

## ✨ Features

- 🧊 **Frosted Mint-Aqua Glass UI:** Calm, modern design featuring multi-tier drop shadows, soft radial light blobs, and pixel-art sprites.
- 🎯 **Interactive Drag-and-Drop:** Marching dotted cyan border with responsive hover, enter, and release feedback.
- 🗂️ **Dedicated Frosted File Card:** Displays file-type badge, cleanly truncated filename, file size in KB/MB, and a quick **"✕"** clear button.
- ⚡ **Instant Fast-Path Engine:**
  - **CSV & TSV:** Automatically converted into clean GitHub Flavored Markdown (GFM) tables in < 15 ms.
  - **Code & Config:** (`.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.yaml`, `.xml`, `.sql`, etc.) wrapped into syntax-highlighted code fences in < 3 ms.
  - **Plain Text / Notes:** Read and output instantaneously.
- 🧠 **Persistent Engine Singleton:** Loads the heavy [Microsoft MarkItDown](https://github.com/microsoft/markitdown) deep-learning models in the background. Complex Office and PDF files convert without reload delays.
- 🔋 **Adaptive Frame Rate:** Intelligently drops to ~4 FPS when the window is inactive or in the background, consuming **0.0% CPU**.
- 📂 **Windows Explorer Integration:** Click the green success status to open Windows Explorer with the converted `.md` file selected automatically.
- 🛡️ **Safe Naming:** Automatic non-destructive output (`filename_converted.md`, `filename_converted2.md`).
- 📦 **Standalone Executable:** Portable standalone binary for Windows 10 and 11.

---

## 📄 Supported Formats

| Category | Formats | Output |
|---|---|---|
| **Office Documents** | `.docx`, `.doc` | Headings, lists, bold/italic, tables |
| **PDF Files** | `.pdf` | Structured text, layouts, extractable tables |
| **Spreadsheets** | `.xlsx`, `.xls` | Markdown data tables |
| **Presentations** | `.pptx`, `.ppt` | Slide text and outlines |
| **Tabular Data** | `.csv`, `.tsv` | Clean GFM Markdown tables (instant fast-path) |
| **Source Code** | `.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.yaml`, `.xml`, `.sql`, etc. | Syntax-highlighted fenced code blocks |
| **Plain Text** | `.txt`, `.log`, `.md` | Direct clean Markdown |

---

## 🚀 Quick Start (No Python Required)

1. Go to the [Releases](../../releases) page and download **`MDrip.exe`**.
2. Run `MDrip.exe` (no installation required).
3. Drag any document or file onto the drop zone (or click to browse).
4. Click **Convert to Markdown**.
5. Click the highlighted link in the status bar to view your new `.md` file in Windows Explorer!

> [!TIP]
> **Windows SmartScreen Note:** Because MDrip is a newly released, free open-source executable, Windows Defender SmartScreen may display an unrecognized app notice on first launch. Click **"More info"** ➔ **"Run anyway"**.

---

## 🛠️ Build from Source

### Prerequisites

- **OS:** Windows 10 or 11
- **Python:** 3.10 or newer

### Setup Steps

```powershell
# 1. Clone the repository
git clone https://github.com/<your-username>/MDrip.git
cd MDrip

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate the UI assets (optional, assets are pre-built)
python assets/generate_assets.py

# 5. Run MDrip in development mode
python app.py

# 6. Package into a standalone .exe
pyinstaller --noconfirm MDrip.spec
```

The compiled binary will be generated in `dist/MDrip.exe`.

---

## 🤝 Contributing

**Contributions are warmly welcome!** Whether you want to add new features, improve conversion quality, fix bugs, or suggest UI enhancements, your help is appreciated.

### Planned Roadmap & Good First Issues

- [ ] **Multi-File Batch Processing:** Convert an entire folder or queue of files in one go.
- [ ] **One-Click "Copy to Clipboard":** Quickly copy converted Markdown without opening the file.
- [ ] **Dark Mode Theme Toggle:** An alternate dark glass theme with deep navy and cyan hues.
- [ ] **Custom Output Folder Selector:** Option to save `.md` files to a designated folder instead of the source directory.
- [ ] **Markdown Previewer:** A lightweight side panel or toggle to preview formatted Markdown.

### How to Contribute

1. **Fork** the repository on GitHub.
2. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes with clear messages:
   ```bash
   git commit -m "Add one-click copy to clipboard action"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request** describing your changes and testing steps.

If you encounter any bugs or have ideas, feel free to [open an issue](../../issues)!

---

## 📁 Repository Structure

```
MDrip/
├── app.py                  # Main GUI (Tkinter + Canvas + Adaptive Loop + Fast-Path)
├── assets/
│   ├── generate_assets.py  # Pillow code-driven vector/pixel asset generator
│   ├── background.png      # Frosted glass background canvas with drop card
│   ├── icon_idle.png       # Pixel-art sequence: Document -> Arrow -> MD badge
│   ├── file_card.png       # Frosted glass card for selected file state
│   ├── icon_doc.png        # Document pixel sprite
│   ├── icon_check.png      # Success checkmark sprite
│   ├── icon_warn.png       # Alert sprite
│   ├── btn_*.png           # Pill buttons (disabled, enabled, hover, pressed, done)
│   └── app_icon.ico        # Multi-size Windows application icon
├── MDrip.spec              # PyInstaller build configuration
├── requirements.txt        # Pinned dependencies
├── test_files/             # Sample test files (.docx, .pdf, .xlsx, .pptx, .csv, .txt)
├── LICENSE                 # MIT License
└── README.md               # Documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for personal and commercial use.

---

## 💖 Acknowledgments

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — Core document conversion engine.
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) — Drag-and-drop bindings for Tkinter.
- [Pillow (PIL)](https://python-pillow.org/) — Anti-aliased graphics and sprite generation.
- [PyInstaller](https://pyinstaller.org/) — Packaging standalone Windows executables.
