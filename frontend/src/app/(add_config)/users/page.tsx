'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Input, Modal, Popconfirm, Select, Space, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { Plus, Edit3, Trash2, Key } from 'lucide-react';
import { useState } from 'react';
import { api } from '@/shared/lib/api';

const { Title } = Typography;

type UserItem = { id: string; username: string; name: string; email: string; role: string; isActive: boolean; createdAt: string };

const roleColor: Record<string, string> = { admin: 'red', reviewer: 'gold', requestor: 'blue' };
const roleOptions = [
  { label: 'Admin', value: 'admin' },
  { label: 'Reviewer', value: 'reviewer' },
  { label: 'Requestor', value: 'requestor' },
];

export default function UserManagementPage() {
  const queryClient = useQueryClient();
  const [messageApi, ctx] = message.useMessage();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<UserItem | null>(null);
  const [pwdModalOpen, setPwdModalOpen] = useState(false);
  const [pwdTarget, setPwdTarget] = useState<UserItem | null>(null);
  const [form, setForm] = useState({ username: '', password: '', name: '', email: '', role: 'requestor' });
  const [newPwd, setNewPwd] = useState('');

  const { data, isLoading } = useQuery({ queryKey: ['users'], queryFn: () => api.get<{ data: UserItem[]; total: number }>('/users') });

  const createMut = useMutation({
    mutationFn: () => api.post('/users', form),
    onSuccess: () => { messageApi.success('User created'); queryClient.invalidateQueries({ queryKey: ['users'] }); closeModal(); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const updateMut = useMutation({
    mutationFn: () => api.put(`/users/${editing!.id}`, { name: form.name, email: form.email, role: form.role }),
    onSuccess: () => { messageApi.success('User updated'); queryClient.invalidateQueries({ queryKey: ['users'] }); closeModal(); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/users/${id}`),
    onSuccess: () => { messageApi.success('User deleted'); queryClient.invalidateQueries({ queryKey: ['users'] }); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const pwdMut = useMutation({
    mutationFn: () => api.put(`/users/${pwdTarget!.id}/password`, { password: newPwd }),
    onSuccess: () => { messageApi.success('Password reset'); setPwdModalOpen(false); setNewPwd(''); },
    onError: (e: Error) => messageApi.error(e.message),
  });

  const closeModal = () => { setModalOpen(false); setEditing(null); setForm({ username: '', password: '', name: '', email: '', role: 'requestor' }); };
  const openCreate = () => { setEditing(null); setForm({ username: '', password: '', name: '', email: '', role: 'requestor' }); setModalOpen(true); };
  const openEdit = (u: UserItem) => { setEditing(u); setForm({ username: u.username, password: '', name: u.name, email: u.email, role: u.role }); setModalOpen(true); };

  const columns: ColumnsType<UserItem> = [
    { title: 'Username', dataIndex: 'username', width: 160, render: (v: string) => <strong>{v}</strong> },
    { title: 'Name', dataIndex: 'name', width: 180 },
    { title: 'Email', dataIndex: 'email', width: 220 },
    { title: 'Role', dataIndex: 'role', width: 100, render: (v: string) => <Tag color={roleColor[v] || 'default'}>{v}</Tag> },
    { title: 'Active', dataIndex: 'isActive', width: 80, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Yes' : 'No'}</Tag> },
    { title: 'Created', dataIndex: 'createdAt', width: 180, render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    {
      title: 'Actions', key: 'actions', width: 180,
      render: (_, r) => (
        <Space>
          <Button size="small" icon={<Edit3 className="h-3 w-3" />} onClick={() => openEdit(r)} />
          <Button size="small" icon={<Key className="h-3 w-3" />} onClick={() => { setPwdTarget(r); setNewPwd(''); setPwdModalOpen(true); }} />
          <Popconfirm title="Delete user?" onConfirm={() => deleteMut.mutate(r.id)}><Button size="small" danger icon={<Trash2 className="h-3 w-3" />} /></Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-6 space-y-4">
      {ctx}
      <div className="flex items-center justify-between">
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>User Management</Title>
          <p className="text-sm text-mdb-steel">Manage local users, roles, and passwords</p>
        </div>
        <Button type="primary" icon={<Plus className="h-4 w-4" />} onClick={openCreate}>Add User</Button>
      </div>
      <Table columns={columns} dataSource={data?.data ?? []} rowKey="id" loading={isLoading} pagination={{ pageSize: 20 }} size="small" />

      <Modal title={editing ? 'Edit User' : 'Add User'} open={modalOpen} onCancel={closeModal} onOk={() => editing ? updateMut.mutate() : createMut.mutate()} confirmLoading={createMut.isPending || updateMut.isPending}>
        <div className="space-y-3 py-2">
          {!editing && <>
            <div><label className="text-sm font-medium">Username</label><Input value={form.username} onChange={e => setForm(p => ({ ...p, username: e.target.value }))} /></div>
            <div><label className="text-sm font-medium">Password</label><Input.Password value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} /></div>
          </>}
          <div><label className="text-sm font-medium">Name</label><Input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} /></div>
          <div><label className="text-sm font-medium">Email</label><Input value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
          <div><label className="text-sm font-medium">Role</label><Select value={form.role} onChange={v => setForm(p => ({ ...p, role: v }))} style={{ width: '100%' }} options={roleOptions} /></div>
        </div>
      </Modal>

      <Modal title="Reset Password" open={pwdModalOpen} onCancel={() => setPwdModalOpen(false)} onOk={() => pwdMut.mutate()} confirmLoading={pwdMut.isPending}>
        <div className="py-2">
          <p className="text-sm text-mdb-steel mb-3">Reset password for <strong>{pwdTarget?.username}</strong></p>
          <Input.Password value={newPwd} onChange={e => setNewPwd(e.target.value)} placeholder="New password (min 6 characters)" />
        </div>
      </Modal>
    </div>
  );
}
