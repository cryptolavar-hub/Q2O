# Research Report: Create a NextJS Web3 UI frontend that allows the monitoring of the blockchain.
**Date**: 2025-11-24T19:53:25.678007
**Task**: task_0002_research - Research: Nextjs Web3
**Depth**: adaptive
**Confidence Score**: 45/100
**Cached**: No

---

## Summary

### Key Findings

- "https://wagmi.sh/react/getting-started",
- "https://www.rainbowkit.com/docs/introduction",
- "https://www.alchemy.com/docs",
- "https://docs.infura.io/infura/networks/ethereum/how-to/connect-to-infura"
- "description": "Next.js setup with wagmi and RainbowKit for wallet connection",
- "code": "import '@rainbow-me/rainbowkit/styles.css';\nimport { getDefaultConfig, RainbowKitProvider } from '@rainbow-me/rainbowkit';\nimport { WagmiProvider } from 'wagmi';\nimport { mainnet, polygon, optimism, arbitrum, base, zora } from 'wagmi/chains';\nimport { QueryClient, QueryClientProvider } from '@tanstack/react-query';\n\nconst config = getDefaultConfig({\n  appName: 'My Next.js Web3 App',\n  projectId: 'YOUR_WALLETCONNECT_PROJECT_ID', // Get from cloud.walletconnect.com\n  chains: [mainnet, polygon, optimism, arbitrum, base, zora],\n  ssr: true, // If using SSR\n});\n\nconst queryClient = new QueryClient();\n\nfunction MyApp({ Component, pageProps }) {\n  return (\n    <WagmiProvider config={config}>\n      <QueryClientProvider client={queryClient}>\n        <RainbowKitProvider>\n          <Component {...pageProps} />\n        </RainbowKitProvider>\n      </QueryClientProvider>\n    </WagmiProvider>\n  );\n}\n\nexport default MyApp;\n"
- "description": "Component for connecting wallet and displaying basic chain info",
- "code": "import { ConnectButton } from '@rainbow-me/rainbowkit';\nimport { useAccount, useNetwork } from 'wagmi';\n\nexport default function WalletStatus() {\n  const { address, isConnected } = useAccount();\n  const { chain } = useNetwork();\n\n  return (\n    <div>\n      <ConnectButton />\n      {isConnected && (\n        <div>\n          <p>Connected to: {address}</p>\n          <p>Network: {chain?.name} (ID: {chain?.id})</p>\n        </div>\n      )}\n      {!isConnected && <p>Please connect your wallet.</p>}\n    </div>\n  );\n}"
- "description": "Monitoring current block number using wagmi hook",
- "code": "import { useBlockNumber } from 'wagmi';\n\nexport default function BlockMonitor() {\n  const { data: blockNumber, isError, isLoading } = useBlockNumber({\n    watch: true, // Continuously watch for new blocks\n    query: { \n      refetchInterval: 5000 // Poll every 5 seconds if watch is not supported or for fallback\n    }\n  });\n\n  if (isLoading) return <div>Fetching block number...</div>;\n  if (isError) return <div>Error fetching block number</div>;\n\n  return (\n    <div>\n      <h2>Current Block Number:</h2>\n      <p>{blockNumber?.toString()}</p>\n    </div>\n  );\n}"

### Official Documentation

- https://docs.ethers.org/v6/",
- https://wagmi.sh/react/getting-started",
- https://nextjs.org/docs",
- https://www.alchemy.com/docs",
- https://docs.infura.io/infura/networks/ethereum/how-to/connect-to-infura"
- https://www.rainbowkit.com/docs/introduction",

### Search Results

---

*Research conducted by ResearcherAgent (researcher_backup)*
*Sources consulted: llm_research_text, llm_research*