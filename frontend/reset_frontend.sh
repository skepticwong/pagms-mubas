#!/bin/bash

echo "🔄 Resetting Frontend Environment..."
echo "=" * 50

# Step 1: Stop any running processes
echo "1. Stopping any running processes..."
pkill -f "vite" 2>/dev/null || true
pkill -f "npm" 2>/dev/null || true
echo "   ✅ Processes stopped"

# Step 2: Clear all caches and build artifacts
echo "2. Clearing caches and build artifacts..."
rm -rf node_modules
rm -rf .vite
rm -rf dist
rm -rf .svelte-kit
echo "   ✅ Caches cleared"

# Step 3: Clear package-lock for fresh install
echo "3. Removing package-lock.json..."
rm -f package-lock.json 2>/dev/null || true
echo "   ✅ Package lock removed"

# Step 4: Fresh npm install
echo "4. Installing dependencies..."
npm install
echo "   ✅ Dependencies installed"

# Step 5: Start development server
echo "5. Starting development server..."
npm run dev
echo "   ✅ Frontend server starting..."

echo ""
echo "🎉 Frontend reset complete!"
echo "📊 Next steps:"
echo "   1. Backend: cd ../backend && python app.py"
echo "   2. Frontend: npm run dev (already running above)"
echo ""
echo "🚀 Both services should be running on:"
echo "   - Backend: http://localhost:5000"
echo "   - Frontend: http://localhost:5173"
echo ""
echo "✨ All Svelte compilation issues should be resolved!"
