const express = require('express');
const { chromium } = require('playwright');

const app = express();
app.use(express.json());

const API_KEY = process.env.API_KEY;

const authenticate = (req, res, next) => {
  const authHeader = req.headers.authorization;
  const token = authHeader && authHeader.split(' ')[1];
  
  if (token !== API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

app.post('/playwright', authenticate, async (req, res) => {
  const { url, waitFor, script, timeout = 30000 } = req.body;

  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });

    const page = await context.newPage();
    await page.goto(url, { waitUntil: 'networkidle', timeout });

    if (waitFor) {
      await page.waitForSelector(waitFor, { timeout: 10000 });
    }

    let result;
    if (script) {
      result = await page.evaluate(script);
    } else {
      result = await page.content();
    }

    await browser.close();

    res.json({
      success: true,
      data: result,
      url,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    if (browser) await browser.close();
    
    res.status(500).json({
      success: false,
      error: error.message,
      url
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'playwright' });
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Playwright scraper listening on port ${PORT}`);
});
