import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Layout, Input, Button, Card, Typography, message, Space, Tag } from 'antd';
import { SendOutlined, LogoutOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import './ChatPage.css';
import remarkGfm from 'remark-gfm';

const { Header, Content, Footer } = Layout;
const { Text } = Typography;

// 已知AI模型名列表
const AI_MODELS = ['DeepSeek', 'GLM'];

function ChatPage() {
  const location = useLocation();
  const roomName = location.state?.roomName || 'MultiMind Chat';
  const { roomId } = useParams();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
  const ws = useRef(null);
  const username = localStorage.getItem('username') || 'Anonymous';

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/');
      return;
    }

    let isMounted = true;
    const wsUrl = `${import.meta.env.VITE_API_BASE.replace('http', 'ws')}/api/chat/ws/${roomId}/${username}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      if (isMounted) message.success('已连接到聊天室');
    };

    ws.current.onmessage = (event) => {
      if (!isMounted) return;
      const raw = event.data;
      // 解析发送者和内容（格式：sender: content）
      const splitIndex = raw.indexOf(': ');
      let sender = '';
      let content = '';
      if (splitIndex !== -1) {
        sender = raw.substring(0, splitIndex);
        content = raw.substring(splitIndex + 2);
      } else {
        // 系统消息
        sender = '系统';
        content = raw;
      }

      // 判断消息类型
      let type = 'other';
      if (sender === username) type = 'me';
      else if (AI_MODELS.includes(sender.replace(/^@/, ''))) type = 'ai';  // 去掉 @ 前缀再匹配
      else if (sender === '系统' || raw.startsWith('[系统]')) type = 'system';

      setMessages(prev => [...prev, {
        sender,
        content,
        type,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }]);
    };

    ws.current.onclose = () => {
      if (isMounted) message.warning('连接断开');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (isMounted) message.error('连接发生错误');
    };

    return () => {
      isMounted = false;
      if (ws.current) ws.current.close();
    };
  }, [navigate, roomId, username]);

  const sendMessage = () => {
    if (inputValue.trim() && ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(inputValue);
      setInputValue('');
    }
  };

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  // 根据消息类型获取气泡样式
  
  const getBubbleStyle = (type) => {
    const base = {
      maxWidth: '70%',
      padding: '8px 14px',
      borderRadius: '12px',
      marginBottom: '8px',
      wordBreak: 'break-word',
      lineHeight: '1.6',
      position: 'relative'
    };
    switch (type) {
      case 'me':
        return { 
          ...base,
          background: '#f0f7ff',          // 淡淡的天蓝
          color: '#003a8c',               // 深蓝色文字，可读性好
          marginLeft: 'auto',
        };

      case 'ai':
        return { 
          ...base,
          background: 'linear-gradient(135deg, #f9f0ff, #f2e6ff)', // 更淡的紫色渐变
          color: '#333',
          border: '1px solid #e0c8ff'
        };

      case 'system':
        return {
           ...base,
          background: '#fffbe6',
          color: '#ad6800',
          textAlign: 'center',
          maxWidth: '100%',
          border: '1px solid #ffe58f'
        };

      case 'other':
      default:
        return {
           ...base,
          background: '#f5f5f5',   // 稍暖的灰色
          color: '#333'
        };
    }
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#001529', padding: '0 24px' }}>
        <Text style={{ color: 'white', fontSize: '18px' }}>{roomName}</Text>
        <Button icon={<LogoutOutlined />} onClick={logout} ghost>退出</Button>
      </Header>
      <Content style={{ padding: '16px', overflowY: 'auto' }}>
        <Card style={{ height: '100%', background: '#fafafa' }} bodyStyle={{ padding: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {messages.map((msg, idx) => (
              <div key={idx} style={{ display: 'flex', flexDirection: 'column', marginBottom: '4px' }}>
                {/* 发送者标识和时间 */}
                {msg.type !== 'system' && (
                  <div style={{
                    display: 'flex',
                    justifyContent: msg.type === 'me' ? 'flex-end' : 'flex-start',
                    marginBottom: '2px',
                    padding: '0 8px'
                  }}>
                    {msg.type === 'ai' && (
                      <Tag icon={<RobotOutlined />} color="purple" style={{ margin: 0 }}>
                        {msg.sender}
                      </Tag>
                    )}
                    {msg.type === 'me' && (
                      <Tag icon={<UserOutlined />} color="blue" style={{ margin: 0 }}>
                        我
                      </Tag>
                    )}
                    {msg.type === 'other' && (
                      <Tag icon={<UserOutlined />} color="green" style={{ margin: 0 }}>
                        {msg.sender}
                      </Tag>
                    )}
                    <Text type="secondary" style={{ fontSize: '10px', marginLeft: '8px' }}>
                      {msg.time}
                    </Text>
                  </div>
                )}
                {/* 消息气泡 */}
                <div style={getBubbleStyle(msg.type)} className={msg.type === 'ai' ? 'ai-message' : ''}>
                  {msg.type === 'system' && <Text strong>{msg.content}</Text>}
                  {msg.type === 'ai' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  ) : (
                    <Text>{msg.content}</Text>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </Content>
      <Footer style={{ background: '#fff', padding: '12px 16px', borderTop: '1px solid #f0f0f0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Button
            type="default"
            onClick={() => {
              setInputValue('@DeepSeek ');
              document.querySelector('input')?.focus();
            }}
          >
            @DeepSeek
          </Button>
          <Button
            type="default"
            onClick={() => {
              setInputValue('@GLM ');
              document.querySelector('input')?.focus();
            }}
          >
            @GLM
          </Button>
          <Input
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onPressEnter={sendMessage}
            placeholder="输入消息，@DeepSeek 或 @GLM 提问"
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