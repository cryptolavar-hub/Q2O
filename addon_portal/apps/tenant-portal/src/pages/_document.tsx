import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta name="description" content="Quick2Odoo Tenant Portal" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <body style={{ margin: 0, padding: 0, boxSizing: 'border-box' }}>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}

