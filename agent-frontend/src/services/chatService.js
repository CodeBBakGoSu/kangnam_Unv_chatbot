/**
 * 채팅 API 서비스
 * 백엔드 API와 통신하여 채팅 세션 생성 및 메시지 전송
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

/**
 * 새 채팅 세션 생성
 * @returns {Promise<{user_id: string, session_id: string}>}
 */
export async function createNewChat() {
  try {
    const response = await fetch(`${API_URL}/chat/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create chat: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      user_id: data.user_id,
      session_id: data.session_id,
    };
  } catch (error) {
    console.error('Error creating new chat:', error);
    throw error;
  }
}

/**
 * 메시지 전송 및 스트리밍 응답 수신
 * @param {string} userId - 사용자 ID
 * @param {string} sessionId - 세션 ID
 * @param {string} message - 전송할 메시지
 * @param {function} onChunk - 청크 수신 시 호출되는 콜백 (text: string)
 * @param {function} onDone - 스트리밍 완료 시 호출되는 콜백
 * @param {function} onError - 에러 발생 시 호출되는 콜백
 */
export async function sendMessage(userId, sessionId, message, onChunk, onDone, onError) {
  try {
    const response = await fetch(`${API_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
    }

    // SSE 스트리밍 응답 처리
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // 디코딩된 텍스트를 버퍼에 추가
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // SSE 라인별로 처리
      const lines = buffer.split('\n');
      
      // 마지막 불완전한 라인은 버퍼에 유지
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.substring(6);
            const data = JSON.parse(jsonStr);

            if (data.done) {
              if (onDone) onDone();
            } else if (data.text) {
              if (onChunk) onChunk(data.text);
            }

            if (data.error) {
              if (onError) onError(data.text || 'Unknown error');
            }
          } catch (e) {
            console.warn('[Streaming] Failed to parse SSE data:', line, e);
          }
        }
      }
    }
    if (onDone) onDone();
  } catch (error) {
    console.error('Error sending message:', error);
    if (onError) {
      onError(error.message || 'Failed to send message');
    }
    throw error;
  }
  } catch (error) {
    console.error('Error in sendMessage:', error);
    if (onError) {
      onError(error.message || 'Failed to send message');
    }
    throw error;
  }
}
