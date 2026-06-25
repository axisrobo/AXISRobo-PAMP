'use client';

import Link from 'next/link';
import { StopOutlined } from '@ant-design/icons';
import { Button } from 'antd';

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <StopOutlined style={{ fontSize: 64, color: '#ff4d4f' }} />
        <h1 className="mt-6 text-2xl font-semibold text-gray-800">Access Denied</h1>
        <p className="mt-2 text-gray-500 max-w-md">
          You do not have permission to access this resource. Please contact your administrator if you believe this is an error.
        </p>
        <div className="mt-6">
          <Link href="/">
            <Button type="primary" size="large">Back to Home</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
