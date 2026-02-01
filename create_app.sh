#!/bin/bash
# Create a simple macOS app wrapper for StockMaker

APP_NAME="StockMaker"
BUNDLE_DIR="${APP_NAME}.app"
CONTENTS_DIR="${BUNDLE_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Clean up old bundle
rm -rf "${BUNDLE_DIR}"

# Create directory structure
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Create the launcher script
cat > "${MACOS_DIR}/${APP_NAME}" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go up: MacOS -> Contents -> StockMaker.app -> stockmaker (project root)
PROJECT_DIR="$( cd "${SCRIPT_DIR}/../../.." && pwd )"
cd "${PROJECT_DIR}"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Python app
python3 run_stockmaker.py
EOF

chmod +x "${MACOS_DIR}/${APP_NAME}"

# Create Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>StockMaker</string>
    <key>CFBundleIdentifier</key>
    <string>com.ubersholder.stockmaker</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>StockMaker</string>
    <key>CFBundleDisplayName</key>
    <string>StockMaker</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ StockMaker.app created successfully!"
echo ""
echo "To run the app:"
echo "  open StockMaker.app"
echo ""
echo "To install to Applications:"
echo "  cp -r StockMaker.app /Applications/"
