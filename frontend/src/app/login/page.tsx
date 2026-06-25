'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Input, Button, Typography, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/shared/lib/auth-context';
import { getAuthToken } from '@/shared/lib/auth-token';

const { Title, Text } = Typography;

export default function LoginPage() {
  const router = useRouter();
  const { login, user, loading: authLoading, error: authError } = useAuth();
  const [messageApi, contextHolder] = message.useMessage();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && user && getAuthToken()) {
      router.replace('/');
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (authError) {
      messageApi.error(authError);
    }
  }, [authError, messageApi]);

  const handleSubmit = async () => {
    if (!username.trim()) {
      messageApi.error('Please enter username');
      return;
    }
    if (!password) {
      messageApi.error('Please enter password');
      return;
    }
    setSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch {
      // error handled by authError effect
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      {contextHolder}
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8 space-y-6">
        <div className="text-center space-y-2">
          <Title level={3} style={{ marginBottom: 0 }}>AxisArch</Title>
          <Text type="secondary">Enterprise Architecture Management</Text>
        </div>

        <div className="space-y-4">
          <Input
            size="large"
            prefix={<UserOutlined />}
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onPressEnter={handleSubmit}
          />
          <Input.Password
            size="large"
            prefix={<LockOutlined />}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onPressEnter={handleSubmit}
          />
          <Button
            type="primary"
            size="large"
            block
            loading={submitting || authLoading}
            onClick={handleSubmit}
          >
            Sign in
          </Button>
        </div>
      </div>
    </div>
  );
}
