import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import * as TaskManager from 'expo-task-manager';
import { Platform } from 'react-native';

const NOTIFICATION_TASK = 'ACTIVITY_REMINDER_TASK';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

const NotificationContext = createContext({});

export const NotificationProvider = ({ children }) => {
  const [notificationEnabled, setNotificationEnabled] = useState(false);
  const [intervalMinutes, setIntervalMinutes] = useState(30);
  const notificationListener = useRef();
  const responseListener = useRef();

  useEffect(() => {
    // Request permissions
    requestPermissions();

    // Set up notification listeners
    notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification received:', notification);
    });

    responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('Notification response:', response);
      // Handle notification tap here
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener.current);
      Notifications.removeNotificationSubscription(responseListener.current);
    };
  }, []);

  const requestPermissions = async () => {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.warn('Notification permissions not granted');
      return false;
    }

    return true;
  };

  const scheduleNotifications = async (enabled = true, minutes = 30) => {
    try {
      // Cancel all existing notifications
      await Notifications.cancelAllScheduledNotificationsAsync();

      if (enabled) {
        // Schedule repeating notification every X minutes
        await Notifications.scheduleNotificationAsync({
          content: {
            title: 'Time to log your activity! 📝',
            body: 'What have you been doing for the past 30 minutes?',
            data: { type: 'activity_reminder' },
          },
          trigger: {
            seconds: minutes * 60,
            repeats: true,
          },
        });

        console.log(`Notifications scheduled every ${minutes} minutes`);
      }

      setNotificationEnabled(enabled);
      setIntervalMinutes(minutes);
    } catch (error) {
      console.error('Failed to schedule notifications:', error);
    }
  };

  const sendImmediateNotification = async () => {
    try {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'Activity Reminder',
          body: 'Time to log your current activity!',
          data: { type: 'activity_reminder' },
        },
        trigger: null, // Send immediately
      });
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  };

  return (
    <NotificationContext.Provider
      value={{
        notificationEnabled,
        intervalMinutes,
        scheduleNotifications,
        sendImmediateNotification,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};
