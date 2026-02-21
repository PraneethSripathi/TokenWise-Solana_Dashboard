# TokenWise: Real-Time Solana Token Intelligence Dashboard 🧠

## Project Overview

TokenWise is a real-time Solana Token Intelligence Dashboard designed to provide dynamic insights into a specific SPL token's ecosystem. It offers a comprehensive view of token holder distribution, real-time transaction activity, and wallet-specific analytics, built to demonstrate key concepts in blockchain data processing and real-time web applications.

## ✨ Features

  * **Dashboard Analytics:** Get an aggregated overview of token activity, including total holders, transaction counts, and overall protocol usage.
  * **Top Token Holders:** See a list of the largest holders of the monitored SPL token, along with their balances and percentage of the total supply.
  * **Real-Time Transaction Feed:** Experience a live stream of token transactions, categorized by action type (buy/sell) and associated protocol, updating dynamically.
  * **Wallet Analysis:** Select a specific wallet from the top holders list to view its recent transaction history and its interaction with various protocols.
  * **Live Monitoring Status:** A visual indicator for WebSocket connection status and backend monitoring activity.
  * **Start/Stop Monitoring:** Controls to initiate or halt the backend's real-time data processing.

-----

## 🚀 Technical Architecture

TokenWise is built with a modern, asynchronous stack to ensure responsiveness and scalability:

### Backend

  * **FastAPI (Python):** For building robust RESTful APIs and managing WebSocket connections.
  * **Motor (AsyncIO MongoDB Driver):** For asynchronous interaction with MongoDB.
  * **MongoDB:** A NoSQL database used for persisting token holder snapshots and transaction history.
  * **aiohttp:** For asynchronous HTTP requests to Solana RPC.
  * **websockets:** For real-time communication with the frontend.

### Frontend

  * **React.js:** A JavaScript library for building the user interface, leveraging functional components and hooks.
  * **Tailwind CSS:** A utility-first CSS framework for rapid and responsive UI styling.
  * **Axios:** For making HTTP requests to the backend API.
  * **WebSockets API:** For consuming real-time transaction updates from the backend.

-----

## 💡 Design and Thought Process

Our core design philosophy was to demonstrate an end-to-end system for blockchain data monitoring, emphasizing real-time capabilities and data visualization.

  * **Modular Backend:** We separated concerns into API routes, WebSocket management, and data processing tasks (WalletManager) to ensure maintainability and scalability.
  * **Asynchronous Operations:** We leveraged Python's `asyncio` and FastAPI's async capabilities for non-blocking I/O, which is crucial for handling concurrent requests and long-running monitoring tasks.
  * **Real-Time User Experience:** Implementing WebSockets was paramount to provide a dynamic and engaging real-time transaction feed, reflecting live blockchain activity (or its simulation).
  * **Data Persistence:** MongoDB was chosen for its flexibility and ability to store semi-structured blockchain data efficiently, allowing for historical querying and dashboard analytics.
  * **Responsive Frontend:** React and Tailwind CSS were selected for their component-based approach and utility-first styling, enabling a clean, modern, and mobile-friendly user interface.

-----

## 🚧 Assumptions and Trade-offs

During the development of TokenWise, we made several real-world constraints and design decisions, particularly regarding blockchain data acquisition:

### Solana RPC Rate Limits

  * **Challenge:** Fetching comprehensive blockchain data, especially using methods like `getProgramAccounts` (essential for discovering all token holders), is highly resource-intensive. Free/public Solana RPC endpoints (e.g., Alchemy's free tier) impose strict rate limits and compute unit restrictions, often leading to `429 Too Many Requests` errors and timeouts.
  * **Trade-off & Approach:** To ensure a functional demonstration despite these limitations, we made the following strategic decisions:
      * **Initial Data Seeding:** The "Top Token Holders" list is initially populated by running a `seed_db.py` script. This pre-populates the MongoDB database with sample data, guaranteeing that the dashboard has content to display from the start, bypassing immediate RPC hurdles.
      * **Mock Real-Time Transactions:** The "Real-Time Transaction Feed" and subsequent wallet-specific transaction history are populated with mock transaction data generated periodically by the backend. This effectively demonstrates WebSocket communication, real-time UI updates, and backend data processing without relying on a constant, high-volume stream of live RPC data, which is often unfeasible on free tiers.
      * **RPC Call Resilience:** The `call_solana_rpc` function in the backend includes retry logic with exponential backoff to handle transient network issues and soft rate limits, showcasing a robust approach to external API interactions. However, for heavily restricted calls like `getProgramAccounts`, it's configured to fail gracefully after a few attempts.

### Full Blockchain Indexing Complexity

  * **Challenge:** Building a production-grade, real-time blockchain indexer that parses all transaction instructions, identifies protocols, and maintains a comprehensive historical database from raw RPC data is a massive engineering undertaking.
  * **Trade-off:** This project focuses on demonstrating the application layer (dashboard, real-time feed, wallet analysis) and the architecture for handling such data, rather than building a full-fledged blockchain indexing solution from scratch. For a production environment, a dedicated blockchain data provider (like Helius, QuickNode, or self-hosting a highly optimized indexing solution) would be essential.

-----

## 🛠️ Setup Instructions and Dependencies

To run TokenWise locally, follow these steps:

### Prerequisites

  * **Python 3.9+**
  * **Node.js 14+**
  * **MongoDB instance** (local or cloud-hosted like MongoDB Atlas)

### 1\. Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Create a `.env` file:**
    Create a file named `.env` in the `backend` directory and add your configuration. Replace the placeholder values with your actual MongoDB connection string and Alchemy RPC/WebSocket URLs.
    ```
    MONGO_URL="YOUR_MONGODB_CONNECTION_STRING"
    DB_NAME="tokenwise_db" # You can choose a different database name
    SOLANA_RPC_URL="https://solana-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"
    SOLANA_WS_URL="wss://solana-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"
    TOKEN_CONTRACT="9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump" # The token contract address to monitor
    ```
    *Note: For `SOLANA_RPC_URL` and `SOLANA_WS_URL`, it's highly recommended to use a dedicated provider like Alchemy or QuickNode to get your API keys. While the project is designed to work around free-tier limitations for demonstration, a dedicated key provides better stability.*
4.  **Seed Initial Data:**
    Run the seeding script to populate your MongoDB with initial top token holders and some mock transaction data. This is crucial for the dashboard to display content immediately.
    ```bash
    python seed_db.py
    ```
    You should see messages indicating that sample holders and tracked wallets have been inserted/updated.
5.  **Run the Backend Server:**
    ```bash
    python server.py
    ```
    The server will start on `http://0.0.0.0:8000`. You will see logs indicating wallet monitoring starting and mock transactions being generated.

### 2\. Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    # OR
    yarn install
    ```
3.  **Create a `.env` file:**
    Create a file named `.env` in the `frontend` directory. This tells React where your backend is running.
    ```
    REACT_APP_BACKEND_URL="http://localhost:8000"
    ```
4.  **Run the Frontend Development Server:**
    ```bash
    npm start
    # OR
    yarn start
    ```
    The frontend application will open in your browser, usually at `http://localhost:3000`.

-----

## 📈 Future Improvements

  * **Integrate with a Paid Blockchain Data API:** Transition from mock data to real, comprehensive real-time transaction streams and historical data by integrating with a robust blockchain data provider (e.g., Helius, QuickNode) that offers advanced indexing and parsing capabilities.
  * **Advanced Transaction Parsing:** Implement more sophisticated logic to parse complex Solana transaction instructions (e.g., DeFi swaps, NFT mints/sales, liquidity pool changes) to provide richer insights beyond simple buys/sells.
  * **Historical Data Visualization:** Add interactive charts and graphs to visualize historical trends for token price, volume, holder growth over time, and protocol usage.
  * **Alerting System:** Develop a notification system (e.g., email, push notifications) for significant events, such as large whale transactions, sudden price movements, or unusual activity.
  * **Multi-Token Support:** Allow users to dynamically add and monitor multiple SPL token contracts through the UI.
  * **User Authentication & Profiles:** Implement a user authentication system to enable personalized dashboards, saved wallet lists, and custom alerts.
  * **Performance Optimizations:** Further optimize database queries, API responses, and frontend rendering for even smoother performance with larger datasets.
