import { ref, onMounted, onUnmounted } from "vue";

export function useWebSocket(endpoint) {
  const isConnected = ref(false);
  const socket = ref(null);
  const reconnectAttempts = ref(0);
  const maxReconnectAttempts = 5;
  const reconnectInterval = ref(null);

  const connect = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found for WebSocket connection");
      return;
    }

    const wsUrl = `ws://localhost:8000/ws/${endpoint}/?token=${token}`;
    socket.value = new WebSocket(wsUrl);

    socket.value.onopen = () => {
      console.log(`✅ WebSocket connected to ${endpoint}`);
      isConnected.value = true;
      reconnectAttempts.value = 0;

      // Limpiar intervalo de reconexión si existe
      if (reconnectInterval.value) {
        clearInterval(reconnectInterval.value);
        reconnectInterval.value = null;
      }
    };

    socket.value.onclose = (event) => {
      console.log(`❌ WebSocket disconnected from ${endpoint}`, event.code);
      isConnected.value = false;

      // Intentar reconectar si no fue un cierre intencional
      if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
        setTimeout(() => {
          reconnectAttempts.value++;
          console.log(`🔄 Attempting to reconnect (${reconnectAttempts.value}/${maxReconnectAttempts})`);
          connect();
        }, 2000 * reconnectAttempts.value);
      }
    };

    socket.value.onerror = (error) => {
      console.error(`❌ WebSocket error on ${endpoint}:`, error);
    };
  };

  const disconnect = () => {
    if (socket.value) {
      socket.value.close(1000); // Cierre normal
      socket.value = null;
    }
    if (reconnectInterval.value) {
      clearInterval(reconnectInterval.value);
      reconnectInterval.value = null;
    }
  };

  const send = (message) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket not connected, cannot send message");
    }
  };

  const onMessage = (callback) => {
    if (socket.value) {
      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          callback(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };
    }
  };

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  return {
    isConnected,
    connect,
    disconnect,
    send,
    onMessage,
  };
}

// Composable específico para notificaciones
export function useNotifications() {
  const notifications = ref([]);
  const unreadCount = ref(0);
  const { isConnected, send, onMessage } = useWebSocket("notificaciones");

  onMessage((data) => {
    switch (data.type) {
      case "notification":
      case "pending_notification":
        notifications.value.unshift(data.data);
        if (!data.data.visto) {
          unreadCount.value++;
        }

        // Mostrar notificación del sistema si está disponible
        if ("Notification" in window && Notification.permission === "granted") {
          new Notification(data.data.tipo, {
            body: data.data.mensaje,
            icon: "/favicon.ico",
          });
        }
        break;

      case "broadcast":
        notifications.value.unshift(data.data);
        break;

      case "unread_count":
        unreadCount.value = data.count;
        break;

      case "connection_established":
        console.log("📡 Notifications WebSocket established");
        // Solicitar contador de no leídas
        send({ type: "get_unread_count" });
        break;
    }
  });

  const markAsRead = (notificationId) => {
    send({
      type: "mark_as_read",
      notification_id: notificationId,
    });

    // Actualizar localmente
    const notification = notifications.value.find((n) => n.id === notificationId);
    if (notification && !notification.visto) {
      notification.visto = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    }
  };

  const requestPermission = async () => {
    if ("Notification" in window && Notification.permission !== "granted") {
      const permission = await Notification.requestPermission();
      return permission === "granted";
    }
    return Notification.permission === "granted";
  };

  return {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    requestPermission,
  };
}

// Composable específico para actualizaciones de animales
export function useAnimalUpdates() {
  const { isConnected, send, onMessage } = useWebSocket("animales");
  const updates = ref([]);

  onMessage((data) => {
    switch (data.type) {
      case "animal_created":
      case "animal_updated":
      case "animal_deleted":
        updates.value.unshift({
          ...data.data,
          timestamp: new Date(),
        });

        // Emitir evento personalizado para que otros componentes puedan escuchar
        window.dispatchEvent(
          new CustomEvent("animalUpdate", {
            detail: data.data,
          })
        );
        break;

      case "connection_established":
        console.log("🐄 Animals WebSocket established");
        break;
    }
  });

  const subscribeToAnimal = (animalId) => {
    send({
      type: "subscribe_animal",
      animal_id: animalId,
    });
  };

  const unsubscribeFromAnimal = (animalId) => {
    send({
      type: "unsubscribe_animal",
      animal_id: animalId,
    });
  };

  return {
    updates,
    isConnected,
    subscribeToAnimal,
    unsubscribeFromAnimal,
  };
}

// Composable específico para logs (solo admins)
export function useLogs() {
  const logs = ref([]);
  const { isConnected, send, onMessage } = useWebSocket("logs");

  onMessage((data) => {
    switch (data.type) {
      case "new_log":
        logs.value.unshift(data.data);
        break;

      case "recent_logs":
      case "filtered_logs":
        logs.value = data.data;
        break;

      case "connection_established":
        console.log("📋 Logs WebSocket established");
        // Solicitar logs recientes
        send({ type: "get_recent_logs", limit: 50 });
        break;
    }
  });

  const getRecentLogs = (limit = 50) => {
    send({ type: "get_recent_logs", limit });
  };

  const filterLogs = (filters) => {
    send({ type: "filter_logs", filters });
  };

  return {
    logs,
    isConnected,
    getRecentLogs,
    filterLogs,
  };
}
