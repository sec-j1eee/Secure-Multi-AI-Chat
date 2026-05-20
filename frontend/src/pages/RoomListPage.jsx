import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, List, Button, Modal, Input, Typography, message } from 'antd';
import { PlusOutlined, LogoutOutlined } from '@ant-design/icons';
import { getRooms, createRoom } from '../api';

const { Header, Content } = Layout;
const { Text } = Typography;

function RoomListPage() {
  const [rooms, setRooms] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const navigate = useNavigate();

  const fetchRooms = async () => {
    try {
      const res = await getRooms();
      setRooms(res.data);
    } catch (err) {
      message.error('获取房间列表失败');
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/');
      return;
    }
    fetchRooms();
  }, [navigate]);

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;
    try {
      await createRoom(newRoomName.trim(), localStorage.getItem('token'));
      message.success('房间创建成功');
      setIsModalOpen(false);
      setNewRoomName('');
      fetchRooms(); // 刷新房间列表
    } catch (err) {
      message.error('创建房间失败');
    }
  };

  const enterRoom = (roomId) => {
    navigate(`/chat/${roomId}`);
  };

  const logout = () => {
    localStorage.clear();
    navigate('/');
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#001529' }}>
        <Text style={{ color: 'white', fontSize: '18px' }}>🤖 AI 群聊大厅</Text>
        <Button icon={<LogoutOutlined />} onClick={logout}>退出</Button>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalOpen(true)}
          style={{ marginBottom: '16px' }}
        >
          创建新房间
        </Button>
        <List
          bordered
          dataSource={rooms}
          renderItem={item => (
            <List.Item
              actions={[<Button type="link" onClick={() => enterRoom(item.id)}>进入</Button>]}
            >
              <List.Item.Meta
                title={item.name}
                description={`房间号: ${item.id}`}
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无聊天室，请创建一个吧！' }}
        />

        <Modal
          title="创建新群聊室"
          open={isModalOpen}
          onOk={handleCreateRoom}
          onCancel={() => setIsModalOpen(false)}
        >
          <Input
            placeholder="请输入房间名称"
            value={newRoomName}
            onChange={e => setNewRoomName(e.target.value)}
            onPressEnter={handleCreateRoom}
          />
        </Modal>
      </Content>
    </Layout>
  );
}

export default RoomListPage;