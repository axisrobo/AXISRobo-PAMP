import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Providers } from './providers';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { ConfigProvider, App } from 'antd';
import { appConfig } from '@/shared/lib/app-config';

const antdTheme = {
  token: {
    colorPrimary: '#4096FF',
    colorSuccess: '#52C41A',
    colorWarning: '#FA8C16',
    colorError: '#E2231A',
    colorBgLayout: '#FAFAFA',
    borderRadius: 6,
    controlHeight: 36,
  },
};

export const metadata: Metadata = {
  title: appConfig.appTitle,
  description: appConfig.appDescription,
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AntdRegistry>
          <ConfigProvider theme={antdTheme}>
            <App>
              <Providers>{children}</Providers>
            </App>
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
