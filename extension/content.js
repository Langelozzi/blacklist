const REDIRECT_URL = "127.0.0.1";
const BLOCKED_KEYWORDS = ["porn"];

/**
 * 1. METADATA SCANNER
 * Checks the 'hidden' parts of the site (title and meta tags) where
 * adult sites often pack SEO keywords.
 */
function scanMetadata() {
    const meta = document.querySelector(
        'meta[name="keywords"], meta[name="description"]',
    );
    const title = document.title.toLowerCase();
    const metaContent = meta ? meta.content.toLowerCase() : "";

    const isSuspicious = BLOCKED_KEYWORDS.some(
        (word) => title.includes(word) || metaContent.includes(word),
    );

    if (isSuspicious) triggerBlock("Metadata Match");
}

/**
 * 2. GOOGLE/BING SAFE SEARCH ENFORCEMENT
 * Forces the browser to stay in SafeSearch mode by checking the URL.
 */
function enforceSafeSearch() {
    const url = window.location.href;
    if (url.includes("google.com/search") && !url.includes("safe=active")) {
        window.location.replace(url + "&safe=active");
    }
    if (url.includes("bing.com/search") && !url.includes("adlt=strict")) {
        window.location.replace(url + "&adlt=strict");
    }
}

/**
 * 3. HEURISTIC TEXT ANALYSIS
 * Instead of looking for any match, we look for a "density"
 * to avoid accidental blocks on educational sites.
 */
function analyzeTextDensity() {
    const text = document.body ? document.body.innerText.toLowerCase() : "";
    let score = 0;

    BLOCKED_KEYWORDS.forEach((word) => {
        if (text.includes(word)) score++;
    });

    // If more than 3 distinct bad keywords are found, block it.
    if (score >= 3) triggerBlock("High Keyword Density");
}

/**
 * 4. DYNAMIC CONTENT MONITOR (MutationObserver)
 * This watches the page for new content being added (like infinite scroll
 * on social media or image galleries).
 */
function startDynamicMonitoring() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                // Only scan new elements that have text
                if (node.nodeType === 1 && node.innerText) {
                    const content = node.innerText.toLowerCase();
                    if (BLOCKED_KEYWORDS.some((word) => content.includes(word))) {
                        triggerBlock("Dynamic Content Match");
                    }
                }
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

function triggerBlock(reason) {
    window.location.replace(REDIRECT_URL);
}

// EXECUTION
enforceSafeSearch();
// Wait for DOM to be ready for text scanning
window.addEventListener("DOMContentLoaded", () => {
    // scanMetadata();
    analyzeTextDensity();
    startDynamicMonitoring();
});
