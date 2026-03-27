#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=== SEO Evolution Loop ==="
echo "Site: ${SITE_URL:-https://meetspot-irq2.onrender.com/}"
echo ""

# Sync latest GSC data (may fail in sandbox -- that's OK)
echo "Syncing GSC data..."
python3 cli.py gsc sync --days 90 2>/dev/null || echo "GSC sync failed, continuing with cached data."

# Show status
python3 cli.py gsc status

# Run evolution
echo ""
echo "Starting evolution loop (mode: ${MODE:-burst})..."
python3 -u cli.py evolve run \
    --site-url "${SITE_URL:-https://meetspot-irq2.onrender.com/}" \
    --max-steps "${MAX_STEPS:-15}" \
    --min-impressions "${MIN_IMPRESSIONS:-1}" \
    --mode "${MODE:-burst}"
