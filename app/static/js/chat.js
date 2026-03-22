(function () {
  const config = window.CHAT_CONFIG || {};
  const roomId = Number(config.roomId || 0);
  const currentUserId = Number(config.currentUserId || 0);

  const box = document.getElementById('chat-box');
  const input = document.getElementById('message-input');
  const form = document.getElementById('chat-send-form');
  const onlineDot = document.querySelector('.online-dot[data-user-id]');

  if (!box || !form || !roomId) return;

  const socket = io();

  const scrollToBottom = () => {
    box.scrollTop = box.scrollHeight;
  };

// C:\DO_AN_TOT_NGHIEP\app\static\js\chat.js
 // Trong chat.js
const renderMessage = (msg) => {
  if (!msg) return;
  const isSelf = Number(msg.sender_id) === currentUserId;
  const div = document.createElement('div');
  div.classList.add('message');
  if (isSelf) div.classList.add('self');

  const now = new Date();
  const timeStr = now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');

  // Thêm logic này để tin nhắn vừa gửi xong hiện "Đã gửi" ngay lập tức
  let statusHtml = '';
  if (isSelf) {
    statusHtml = `<span class="status-icon"><i class="status-text">Đã gửi</i></span>`;
  }

div.innerHTML = `
  <div class="bubble-wrapper">
    <div class="bubble"></div>
    <div class="msg-status">
      <span class="time">${timeStr}</span>
      ${statusHtml}
    </div>
  </div>
`;
div.querySelector('.bubble').textContent = msg.content || '[Hình ảnh]';

  box.appendChild(div);
  scrollToBottom();
};

// Lắng nghe sự kiện Đã xem từ Socket
socket.on('messages_seen', (payload) => {
  if (Number(payload.room_id) === roomId) {
    // Tìm tất cả các tin nhắn "Đã gửi" của mình và đổi thành "Đã xem"
    document.querySelectorAll('.message.self .status-icon:not(.is-seen)').forEach(icon => {
      icon.classList.add('is-seen');
      icon.querySelector('.status-text').textContent = 'Đã xem';
    });
  }
});

  socket.on('connect', () => {
    socket.emit('join_room', { room_id: roomId });
    fetch((config.seenUrlTemplate || '/chat/seen/0').replace('/0', `/${roomId}`), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    }).catch(() => null);
  });

  socket.on('receive_message', (message) => {
    if (Number(message.room_id) !== roomId) return;
    renderMessage(message);
  });

  socket.on('user_online', (payload) => {
    if (onlineDot && Number(onlineDot.dataset.userId) === Number(payload.user_id)) {
      onlineDot.classList.add('is-online');
    }
  });
 socket.on('user_offline', (payload) => {
    if (onlineDot && Number(onlineDot.dataset.userId) === Number(payload.user_id)) {
      onlineDot.classList.remove('is-online');
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const content = (input.value || '').trim();
    if (!content) return;

    const response = await fetch('/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        room_id: roomId,
        content,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      alert(payload.error || 'Không thể gửi tin nhắn');
      return;
    }


    socket.emit('send_message', {
      room_id: roomId,
      message: payload,
    });

    input.value = '';
    input.focus();
  });

  scrollToBottom();
})();