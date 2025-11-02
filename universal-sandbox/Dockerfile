# Multi-runtime scraper sandbox
FROM ubuntu:24.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    ca-certificates \
    gnupg \
    build-essential \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    ruby \
    ruby-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# Install Go 1.22
RUN wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz \
    && rm go1.22.0.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH="/root/go"
ENV PATH="$GOPATH/bin:$PATH"

# Install common Node.js scraping l

cat > ~/docker-scrapers/universal-sandbox/Dockerfile << 'EOF'
# Multi-runtime scraper sandbox
FROM ubuntu:24.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    ca-certificates \
    gnupg \
    build-essential \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    ruby \
    ruby-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

# Install Go 1.22
RUN wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz \
    && rm go1.22.0.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:$PATH"
ENV GOPATH="/root/go"
ENV PATH="$GOPATH/bin:$PATH"

# Install common Node.js scraping libraries globally
RUN npm install -g \
    crawlee \
    puppeteer \
    playwright \
    cheerio \
    axios \
    jsdom \
    @mozilla/readability

# Install Playwright browsers
RUN npx playwright install-deps chromium \
    && npx playwright install chromium

# Install common Python scraping libraries
RUN pip3 install --no-cache-dir \
    scrapy \
    beautifulsoup4 \
    lxml \
    requests \
    selenium \
    playwright \
    httpx \
    parsel \
    pyquery

# Install Python Playwright browsers
RUN python3 -m playwright install chromium

# Install common Ruby gems
RUN gem install nokogiri mechanize httparty

# Install common Go packages
RUN go install github.com/gocolly/colly/v2@latest

# Copy executor script
COPY executor.py requirements.txt ./

# Install Python dependencies for the executor
RUN pip3 install --no-cache-dir -r requirements.txt

# Create temp directory for repos
RUN mkdir -p /tmp/scrapers

EXPOSE 8000

CMD ["python3", "executor.py"]
