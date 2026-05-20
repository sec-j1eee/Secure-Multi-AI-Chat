import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Tabs, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { register, login } from '../api';

function LoginPage() {
  const [activeTab, setActiveTab] = useState('login');
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    try {
      const { username, password } = values;
      const res = activeTab === 'login'
        ? await login(username, password)
        : await register(username, password);
      
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('username', username);
      message.success(activeTab === 'login' ? '登录成功' : '注册成功');
      navigate('/rooms');
    } catch (err) {
      message.error(err.response?.data?.detail || '操作失败');
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Secure-Multi-AI-Chat</h2>
        <Tabs activeKey={activeTab} onChange={setActiveTab} centered>
          <Tabs.TabPane tab="登录" key="login" />
          <Tabs.TabPane tab="注册" key="register" />
        </Tabs>
        <Form onFinish={handleSubmit} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" maxLength={72} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              {activeTab === 'login' ? '登录' : '注册'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default LoginPage;