import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Input, Button, List, Card, Typography, message, Space } from 'antd';
import { SendOutlined, LogoutOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';

const { Header, Content, Footer } = Layout;
const { Text } = Typography;


function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
  const ws = useRef(null);
  const username = localStorage.getItem('username') || 'Anonymous';
  const { roomId } = useParams(); 

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/');
      return;
    }

    let isMounted = true;

    // 创建 WebSocket 连接
    ws.current = new WebSocket(`ws://localhost:8000/api/chat/ws/${roomId}/${username}`);

    ws.current.onopen = () => {
      if (isMounted) {
        message.success('已连接到聊天室');
      }
    };

    ws.current.onmessage = (event) => {
      if (isMounted) {
        setMessages(prev => [...prev, { content: event.data, type: 'received' }]);
      }
    };

    ws.current.onclose = () => {
      if (isMounted) {
        message.warning('连接断开');
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (isMounted) {
        message.error('连接发生错误');
      }
    };

    // 组件卸载时清理
    return () => {
      isMounted = false;
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [navigate, roomId, username]);

  const sendMessage = () => {
    if (inputValue.trim() && ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(inputValue);
      setMessages(prev => [...prev, { content: `我: ${inputValue}`, type: 'sent' }]);
      setInputValue('');
    }
  };

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#001529' }}>
        <Text style={{ color: 'white', fontSize: '18px' }}>🤖 AI 群聊室</Text>
        <Button icon={<LogoutOutlined />} onClick={logout}>退出</Button>
      </Header>
      <Content style={{ padding: '16px', overflowY: 'auto' }}>
        <Card style={{ height: '100%' }}>
          <List
            dataSource={messages}
            renderItem={item => (
              <List.Item style={{ border: 'none', padding: '4px 0' }}>
                <Text style={{
                  background: item.type === 'sent' ? '#e6f7ff' : '#f6ffed',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  display: 'inline-block',
                  wordBreak: 'break-word'
                }}>
                  {item.content}
                </Text>
              </List.Item>
            )}
          />
        </Card>
      </Content>
      <Footer style={{ background: '#fff', padding: '12px 16px' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onPressEnter={sendMessage}
            placeholder="输入消息，例如 @DeepSeek 你好"
            size="large"
          />
          <Button type="primary" icon={<SendOutlined />} onClick={sendMessage} size="large">
            发送
          </Button>
        </Space.Compact>
      </Footer>
    </Layout>
  );
}

export default ChatPage;