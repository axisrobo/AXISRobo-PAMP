'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { Button, Result } from 'antd';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Route error boundary caught:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Result
        status="error"
        title="Something went wrong"
        subTitle={error?.message || 'An unexpected error occurred while rendering this page.'}
        extra={[
          <Button type="primary" key="retry" onClick={() => reset()}>
            Try again
          </Button>,
          <Link href="/" key="home">
            <Button>Back to Home</Button>
          </Link>,
        ]}
      />
    </div>
  );
}
