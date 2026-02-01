# StockMaker - Stock Image CSV Generator

A native macOS application for generating optimized CSV files for stock image platforms (Adobe Stock, Shutterstock). Features AI-powered keyword generation and image description creation using local Ollama models.

## ✨ Features

- **Drag-and-Drop Interface** - Simple image selection with visual feedback
- **AI-Powered Keywords** - Generates 15-40 relevant keywords per image using Qwen3-VL
- **Image Descriptions** - Creates stock-optimized titles and descriptions
- **Dual CSV Export** - Adobe Stock and Shutterstock formatted files
- **Beautiful Dark Theme** - Gruvbox color scheme with smooth animations
- **Auto-Ollama Management** - Automatically starts/detects local Ollama service
- **Blur-to-Clear Animation** - Thumbnails blur on load, clear over 60 seconds
- **Fallback Processing** - Extracts keywords from descriptions if API fails

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install Ollama (handles AI processing)
# Download: https://ollama.ai

# Python 3.9+ (usually pre-installed on macOS)
python3 --version
```

### 2. Setup
```bash
cd /path/to/stockmaker
pip3 install PyQt6 requests
```

### 3. Create & Run the App
```bash
chmod +x create_app.sh
./create_app.sh
open StockMaker.app
```

### 4. Install to Applications (Optional)
```bash
cp -r StockMaker.app /Applications/
open /Applications/StockMaker.app
```

## 📚 Usage

### Workflow
1. **Drag images** onto the StockMaker window (JPG, PNG, GIF, BMP)
2. **View thumbnails** - Images appear with blur animation
3. **Click "Process Images"** - App generates keywords and descriptions
4. **Review CSV files** - Check output in your project folder:
   - `adobe_stock_upload.csv`
   - `shutterstock_upload.csv`

### Generated Data
For each image, the app generates:
- **Keywords**: 15-40 relevant search terms
- **Title**: Stock-optimized description
- **Categories**: Shutterstock category mapping
- **Editorial/Mature Flags**: Pre-configured defaults

## 🏗️ Architecture

```
┌─────────────┐
│   PyQt6     │  Desktop GUI with drag-drop
│   (app_qt)  │  
└──────┬──────┘
       │
       ├─→ ┌─────────────┐
       │   │   Ollama    │  Handles Qwen3-VL model
       │   │ (localhost) │  (auto-start on app launch)
       │   └────┬────────┘
       │        │
       └─→ ┌────┴────────┐
           │  main.py    │  Image processing
           │  (backend)  │  Generates: keywords,
           └─────┬───────┘  descriptions, categories
                 │
                 ├─→ adobe_stock_upload.csv
                 └─→ shutterstock_upload.csv
```

## 📖 Documentation

- **[BUILD_GUIDE.md](BUILD_GUIDE.md)** - Detailed setup, troubleshooting, customization
- **[app_qt.py](app_qt.py)** - PyQt6 GUI (530+ lines)
- **[main.py](main.py)** - Image processing backend
- **[run_stockmaker.py](run_stockmaker.py)** - Ollama launcher

## ⚙️ Configuration

### Default Settings
| Setting | Value | File |
|---------|-------|------|
| Model | `qwen3-vl:4b` | [main.py](main.py#L8) |
| API URL | `http://localhost:11434` | [main.py](main.py#L9) |
| Theme | Gruvbox Dark | [app_qt.py](app_qt.py#L25) |
| Blur Duration | 60 seconds | [app_qt.py](app_qt.py#L230) |
| Window Size | 1400x900 px | [app_qt.py](app_qt.py#L15) |

### Customization Examples

**Change the AI model:**
```python
# main.py line 8
MODEL = "llava:latest"  # or any Ollama-compatible model
```

**Use remote Ollama server:**
```python
# main.py line 9
API_URL = "http://192.168.1.100:11434"
```

**Disable blur animation:**
```python
# app_qt.py line 220
# Comment out: blur_effect = ...
```

## 🔧 Troubleshooting

### App won't start
```bash
# Check Python
python3 --version  # Should be 3.9+

# Check PyQt6
python3 -c "import PyQt6" # Should work

# Run with debug output
source venv/bin/activate  # If using venv
python3 run_stockmaker.py
```

### Ollama issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama manually
ollama serve

# Pull the model
ollama pull qwen3-vl:4b
```

### Model not found
```bash
# List available models
ollama list

# Download the default model
ollama pull qwen3-vl:4b
```

See [BUILD_GUIDE.md](BUILD_GUIDE.md#troubleshooting) for more solutions.

## 📦 File Structure

```
stockmaker/
├── README.md              # This file
├── BUILD_GUIDE.md         # Installation & troubleshooting
├── app_qt.py              # PyQt6 GUI application (533 lines)
├── main.py                # Image processing backend
├── run_stockmaker.py      # App launcher with Ollama management
├── create_app.sh          # macOS app bundle creation script
├── requirements.txt       # Python dependencies
├── StockMaker.app/        # (Generated) Native macOS app
├── venv/                  # (Optional) Python virtual environment
├── adobe_stock_upload.csv # Output file
├── shutterstock_upload.csv# Output file
└── __pycache__/          # Python cache
```

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| macOS | 10.13+ | 11.0+ |
| Python | 3.9 | 3.11+ |
| RAM | 4 GB | 8+ GB |
| Storage | 3 GB | 5+ GB (for models) |
| Ollama | Required | Latest version |

## 🎨 UI Features

### Gruvbox Dark Theme
- **Dark background**: `#282828`
- **Orange accents**: `#fda029`
- **Text colors**: Readable light grays
- **Smooth animations**: 60-second blur-to-clear effect

### Responsive Layout
- **Left panel**: Image drop zone & thumbnail (33% width)
- **Right panel**: Processing log & status (67% width)
- **Auto-scaling**: Adapts to image aspect ratios (16:9)

## 🔄 Processing Pipeline

1. **Image Ingestion** - Accepts JPG, PNG, GIF, BMP
2. **Thumbnail Generation** - Creates 840x471px preview (16:9 ratio)
3. **Blur Animation** - Applies QGraphicsBlurEffect over 60 seconds
4. **Background Processing** - Sends to Ollama (non-blocking)
5. **Keyword Generation** - With fallback extraction from descriptions
6. **Description Creation** - Stock-optimized titles
7. **Category Inference** - Maps to Shutterstock categories
8. **CSV Export** - Two formats for different platforms

## 📊 Performance

| Operation | Duration | Notes |
|-----------|----------|-------|
| App startup | 2-3 sec | Subsequent launches after first |
| Ollama startup | 10-30 sec | First time, then in memory |
| Thumbnail generation | <100ms | Per image |
| AI processing | 2-5 sec | Per image (depends on content) |
| CSV export | <100ms | Both files |

## 🛠️ Development

### Project Tools
- **PyQt6** - Desktop GUI framework
- **Ollama** - Local AI backend (qwen3-vl:4b)
- **Requests** - HTTP client for API calls
- **Base64** - Image encoding for API

### Key Code Sections
- [UI Setup](app_qt.py#L15-L40) - Window initialization
- [Drag-Drop](app_qt.py#L80-L120) - File handling
- [Animation](app_qt.py#L220-L250) - Blur effect
- [Keywords](main.py#L30-L60) - AI generation
- [CSV Output](main.py#L100-L150) - File export

### Testing
```bash
# Run the app in debug mode
python3 -u run_stockmaker.py

# Test Ollama connectivity
curl http://localhost:11434/api/tags

# Test image processing
python3 -c "from main import generate_image_keywords; print(generate_image_keywords('test.jpg'))"
```

## 🚀 Deployment

### macOS App Store (Future)
- Code signing required
- Notarization process
- Different bundle identifier

### Distribution
```bash
# Create DMG installer (optional)
hdiutil create -volname StockMaker -srcfolder StockMaker.app stockmaker.dmg

# Share the .app directly
zip -r StockMaker.app.zip StockMaker.app
```

## 📝 License

This project is provided as-is for personal and commercial use.

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- [ ] Windows/Linux support (with PyQt6)
- [ ] Cloud Ollama deployment
- [ ] Batch processing optimization
- [ ] Custom keyword templates
- [ ] Additional stock platforms
- [ ] Image preview galleries

## 📞 Support

For issues:
1. Check [BUILD_GUIDE.md](BUILD_GUIDE.md#troubleshooting)
2. Run from terminal for debug output: `python3 run_stockmaker.py`
3. Verify Ollama: `curl http://localhost:11434/api/tags`
4. Check prerequisites: Python 3.9+, PyQt6, Ollama installed

---

**StockMaker** — Simplifying stock image preparation 🎉

Version 1.0 | macOS Native App | AI-Powered CSV Generation
