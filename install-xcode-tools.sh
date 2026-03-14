#!/bin/bash
set -euo pipefail

# Install Xcode Command Line Tools
if xcode-select -p &>/dev/null; then
  echo "Xcode Command Line Tools are already installed at: $(xcode-select -p)"
  exit 0
fi

echo "Installing Xcode Command Line Tools..."
xcode-select --install

# Wait for installation to complete
echo "Waiting for installation to complete..."
until xcode-select -p &>/dev/null; do
  sleep 5
done

echo "Xcode Command Line Tools installed successfully at: $(xcode-select -p)"
