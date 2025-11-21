import type { AppProps } from 'next/app';
import { Provider } from 'urql';
import { graphqlClient } from '../lib/graphql';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <Provider value={graphqlClient}>
      <Component {...pageProps} />
    </Provider>
  );
}

