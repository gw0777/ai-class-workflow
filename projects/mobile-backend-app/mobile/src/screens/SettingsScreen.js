import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { List, Switch, Button, Title, Divider } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';

export default function SettingsScreen() {
  const { user, logout, updateUser } = useAuth();
  const { notificationEnabled, scheduleNotifications } = useNotifications();
  const [localNotificationEnabled, setLocalNotificationEnabled] = useState(notificationEnabled);

  const handleNotificationToggle = async () => {
    const newValue = !localNotificationEnabled;
    setLocalNotificationEnabled(newValue);
    await scheduleNotifications(newValue, 30);

    // Also update backend
    await updateUser({ notification_enabled: newValue });
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: logout,
      },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>Settings</Title>
      </View>

      <List.Section>
        <List.Subheader>Account</List.Subheader>
        <List.Item
          title="Username"
          description={user?.username}
          left={(props) => <List.Icon {...props} icon="account" />}
        />
        <List.Item
          title="Email"
          description={user?.email}
          left={(props) => <List.Icon {...props} icon="email" />}
        />
      </List.Section>

      <Divider />

      <List.Section>
        <List.Subheader>Notifications</List.Subheader>
        <List.Item
          title="Activity Reminders"
          description="Get reminded every 30 minutes to log your activity"
          left={(props) => <List.Icon {...props} icon="bell" />}
          right={() => (
            <Switch value={localNotificationEnabled} onValueChange={handleNotificationToggle} />
          )}
        />
      </List.Section>

      <Divider />

      <List.Section>
        <List.Subheader>Data</List.Subheader>
        <List.Item
          title="Export Data"
          description="Download your activity data"
          left={(props) => <List.Icon {...props} icon="download" />}
          onPress={() => Alert.alert('Coming Soon', 'This feature is under development')}
        />
        <List.Item
          title="Delete Account"
          description="Permanently delete your account and data"
          left={(props) => <List.Icon {...props} icon="delete" />}
          onPress={() =>
            Alert.alert(
              'Delete Account',
              'Are you sure? This action cannot be undone.',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Delete',
                  style: 'destructive',
                  onPress: () => Alert.alert('Coming Soon', 'This feature is under development'),
                },
              ]
            )
          }
        />
      </List.Section>

      <View style={styles.logoutContainer}>
        <Button mode="outlined" onPress={handleLogout} style={styles.logoutButton}>
          Logout
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#6200ee',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  logoutContainer: {
    padding: 20,
  },
  logoutButton: {
    borderColor: '#d32f2f',
  },
});
