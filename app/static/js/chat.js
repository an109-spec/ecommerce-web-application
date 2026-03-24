(function () {
  const config = window.CHAT_CONFIG || {};
  const roomId = Number(config.roomId || 0);
  const currentUserId = Number(config.currentUserId || 0);

  const box = document.getElementById('chat-box');
  const input = document.getElementById('message-input');
  const imageInput = document.getElementById('chat-image-input');
  const form = document.getElementById('chat-send-form');
  const onlineDot = document.querySelector('.online-dot[data-user-id]');

  if (!box || !form || !roomId) return;

  const socket = io();

  const scrollToBottom = () => {
    box.scrollTop = box.scrollHeight;
  };

  const formatMessageTime = (value) => {
    if (!value) return '';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '';
    const day = parsed.getDate().toString().padStart(2, '0');
    const month = (parsed.getMonth() + 1).toString().padStart(2, '0');
    const year = parsed.getFullYear();
    const hour = parsed.getHours().toString().padStart(2, '0');
    const minute = parsed.getMinutes().toString().padStart(2, '0');
    return `${day}/${month}/${year} ${hour}:${minute}`;
  };

  const renderMessage = (msg) => {
    if (!msg) return;
    const isSelf = Number(msg.sender_id) === currentUserId;
    const timeStr = formatMessageTime(msg.created_at);

    const div = document.createElement('div');
    div.classList.add('message');
    if (isSelf) div.classList.add('self');
    div.dataset.msgId = msg.id || '';

    let statusHtml = '';
    if (isSelf) {
      const isSeen = !!msg.seen;
      statusHtml = `<span class="status-icon ${isSeen ? 'is-seen' : ''}"><i class="status-text">${isSeen ? 'Đã xem' : 'Đã gửi'}</i></span>`;
    }

    const contentText = msg.content ? `<div>${msg.content}</div>` : '';
    const imageHtml = msg.image ? `<img class="chat-image" src="${msg.image}" alt="Ảnh đính kèm">` : '';
    const fallbackText = !msg.image ? (msg.content || '[Hình ảnh]') : '';

    div.innerHTML = `
      <div class="bubble-wrapper">
        <div class="bubble">${contentText || fallbackText}${imageHtml}</div>
        <div class="msg-status">
          <span class="time">${timeStr}</span>
          ${statusHtml}
        </div>
      </div>
    `;

    box.appendChild(div);
    scrollToBottom();
  };

  socket.on('messages_seen', (payload) => {
    if (Number(payload.room_id) === roomId) {
      document.querySelectorAll('.message.self .status-icon:not(.is-seen)').forEach((icon) => {
        icon.classList.add('is-seen');
        const text = icon.querySelector('.status-text');
        if (text) text.textContent = 'Đã xem';
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

  const uploadImage = async (file) => {
    const fd = new FormData();
    fd.append('image', file);
    const response = await fetch('/chat/upload-image', {
      method: 'POST',
      body: fd,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || 'Không thể tải ảnh lên');
    }
    return payload.image || '';
  };


  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const content = (input.value || '').trim();
    const imageFile = imageInput?.files?.[0] || null;

    if (!content && !imageFile) return;

    let image = '';
    try {
      if (imageFile) {
        image = await uploadImage(imageFile);
      }
    } catch (error) {
      alert(error.message || 'Không thể tải ảnh lên');
      return;
    }

    const response = await fetch('/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        room_id: roomId,
        content,
        image,
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
    if (imageInput) imageInput.value = '';
    input.focus();
  });

  scrollToBottom();
})();