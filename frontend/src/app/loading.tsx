import { Spin } from 'antd';

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <Spin size="large" />
        <p className="mt-4 text-gray-500">Loading...</p>
      </div>
    </div>
  );
}
