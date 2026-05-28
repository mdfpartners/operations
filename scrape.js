const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

async function scrape() {
  const url = 'http://www.logicalsysinc.com/';
  let html;
  try {
    const res = await axios.get(url, { timeout: 15000, headers: { 'User-Agent': 'Mozilla/5.0' } });
    html = res.data;
  } catch(e) {
    console.log('SCRAPE_FAILED:' + e.message);
    process.exit(1);
  }

  const $ = cheerio.load(html);

  // Extract brand info
  const title = $('title').text().trim();
  const metaDesc = $('meta[name="description"]').attr('content') || '';
  const ogDesc = $('meta[property="og:description"]').attr('content') || '';
  const h1 = $('h1').first().text().trim();

  // Color extraction from inline styles / CSS vars
  const inlineStyles = $('[style]').map((i,el) => $(el).attr('style')).get().join(' ');
  const hexMatches = inlineStyles.match(/#([0-9a-fA-F]{6})/g) || [];
  const freq = {};
  hexMatches.forEach(h => freq[h] = (freq[h]||0)+1);
  const topColor = Object.entries(freq).sort((a,b)=>b[1]-a[1])[0];

  // Image search
  let imageUrl = null;
  const ogImage = $('meta[property="og:image"]').attr('content');
  if (ogImage) imageUrl = ogImage;

  if (!imageUrl) {
    const heroImg = $('header img, .hero img, #hero img, [class*="banner"] img').first().attr('src');
    if (heroImg) imageUrl = heroImg;
  }

  if (!imageUrl) {
    $('img').each((i, el) => {
      if (imageUrl) return;
      const src = $(el).attr('src') || '';
      const w = parseInt($(el).attr('width') || '0');
      if (w > 600 || /hero|banner|cover|bg/i.test(src)) imageUrl = src;
    });
  }

  // Make absolute
  if (imageUrl && !imageUrl.startsWith('http')) {
    imageUrl = new URL(imageUrl, url).href;
  }

  // Collect body text for industry insights
  const bodyText = $('p').map((i,el) => $(el).text().trim()).get().filter(t => t.length > 40).slice(0, 6).join(' | ');

  console.log(JSON.stringify({
    title, h1, metaDesc, ogDesc, imageUrl,
    primaryColor: topColor ? topColor[0].replace('#','') : null,
    bodyText
  }));
}

scrape();
