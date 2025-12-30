# Plan: Direct Odoo Image URLs

## Goal
Eliminate Flask as a bottleneck for image loading by using direct Odoo URLs.

## Current State

```
Browser → Flask (single-threaded) → Odoo RPC → PostgreSQL
                ↓
         ~400ms per image
         Blocks other requests
```

**Current image fetch flow:**
1. Frontend calls `/decilo-api/variant-image/{id}` or `/products/{id}/variant-image`
2. Flask makes RPC to Odoo
3. Odoo queries PostgreSQL for base64 image
4. Flask returns image to browser

**Problems:**
- Flask dev server is single-threaded (requests queue up)
- RPC overhead (~120ms per call)
- Base64 encoding/decoding overhead
- Exclusions request can block image request

## Proposed State

```
Browser → Odoo Web Server (direct HTTP)
                ↓
         ~50-100ms (just HTTP GET)
         No Flask involvement
```

**Direct URL format (tested and working):**
```
https://decilo.odoo.com/web/image/product.product/{variant_id}/image_512
```

**Size options:**
| Size | Field | Use Case |
|------|-------|----------|
| `image_256` | Thumbnail | Grid view |
| `image_512` | Medium | Initial checkout display |
| `image_1024` | Large | Zoom view |
| `image_1920` | Full | High-res display |

## Implementation Steps

### Step 1: Add Odoo URL to Configuration

**File:** `decilo.py` or frontend config

Add the Odoo base URL as a configuration that frontend can access:
```javascript
// Could be injected into the page or fetched from an endpoint
const ODOO_BASE_URL = 'https://decilo.odoo.com';
```

### Step 2: Create Image URL Helper Function

**File:** `static/vue/decilo_checkout.vue`

```javascript
getDirectImageUrl(variantProductId, size = 'image_512') {
  if (!variantProductId) return null;
  return `${ODOO_BASE_URL}/web/image/product.product/${variantProductId}/${size}`;
}
```

### Step 3: Update selectedProduct Watcher

**File:** `static/vue/decilo_checkout.vue`

Change from:
```javascript
this.fetchImageByVariantId(variantId, 'medium').then(...)
```

To:
```javascript
// Instant - no fetch needed, just set the URL
this.activeImageUrl = this.getDirectImageUrl(variantId, 'image_512');
this.isImageLoading = false;
```

### Step 4: Update refreshVariantImage for Variant Changes

**File:** `static/vue/decilo_checkout.vue`

When user changes variant selection, we still need to resolve the new variant ID. Two options:

**Option A: Keep using Flask for variant resolution only**
- POST to `/products/{id}/variant-image` but only get `variant_product_id` back
- Then use direct URL for image

**Option B: Return variant_product_id from a lightweight endpoint**
- Create new endpoint that just resolves variant (no image)
- Use direct URL for image

### Step 5: Handle Fallback for Missing Images

Direct URLs return a placeholder if image doesn't exist. Add error handling:
```javascript
<img
  :src="activeImageUrl"
  @error="handleImageError"
/>
```

### Step 6: Remove Unused Flask Image Endpoints (Optional Cleanup)

After migration, these endpoints become unused:
- `/decilo-api/variant-image/<int:variant_product_id>` (the new one we just added)
- Could keep `/decilo-api/products/<int:product_id>/variant-image` for variant resolution

---

## Files to Modify

| File | Changes |
|------|---------|
| `static/vue/decilo_checkout.vue` | Use direct URLs, remove fetch calls |
| `static/vue/decilo_product_catalog.vue` | Pass Odoo URL to checkout (or use global config) |
| `decilo.py` (optional) | Add endpoint to expose ODOO_URL to frontend |

---

## RPC Comparison

### Before (Current)
| Action | RPCs | Time |
|--------|------|------|
| Product details | 3 | ~400ms |
| Image (via Flask) | 1+ | ~400ms |
| **Total** | **4+** | **~800ms** |

### After (Direct URLs)
| Action | RPCs | Time |
|--------|------|------|
| Product details | 3 | ~400ms |
| Image (direct URL) | 0 | ~50ms |
| **Total** | **3** | **~450ms** |

**Savings: ~350ms per image load, plus no Flask blocking**

---

## Risk Considerations

1. **Odoo URL exposed to frontend**
   - Low risk: Image URLs are typically public
   - Only exposes product images, not sensitive data

2. **CORS issues**
   - Test: Odoo may need CORS headers for cross-origin requests
   - Mitigation: Images loaded via `<img>` tag don't require CORS

3. **Odoo availability**
   - If Odoo is down, images won't load
   - Same as current situation (Flask calls Odoo anyway)

4. **Caching**
   - Browser will cache images by URL
   - May need cache-busting if images change frequently

---

## Testing Plan

1. Verify direct URL works in browser (not just curl/python)
2. Test CORS if using fetch() instead of <img> tag
3. Test with different image sizes
4. Test fallback when variant has no image
5. Performance comparison: measure time to first image display
