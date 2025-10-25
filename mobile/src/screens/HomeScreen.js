import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Title, Card, Text, Button } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { activityAPI } from '../services/api';

export default function HomeScreen({ navigation }) {
  const { user } = useAuth();
  const { notificationEnabled, scheduleNotifications } = useNotifications();
  const [todayActivities, setTodayActivities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTodayActivities();
  }, []);

  const loadTodayActivities = async () => {
    setLoading(true);
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const response = await activityAPI.getAll({
        start_date: today.toISOString(),
        page: 1,
        page_size: 10,
      });

      setTodayActivities(response.data.items);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNotifications = async () => {
    await scheduleNotifications(!notificationEnabled, 30);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>Welcome, {user?.username}!</Title>
        <Text style={styles.subtitle}>Track your daily activities</Text>
      </View>

      <Card style={styles.card}>
        <Card.Title title="Notifications" />
        <Card.Content>
          <Text>
            Status: {notificationEnabled ? 'Enabled (every 30 min)' : 'Disabled'}
          </Text>
        </Card.Content>
        <Card.Actions>
          <Button onPress={toggleNotifications}>
            {notificationEnabled ? 'Disable' : 'Enable'} Notifications
          </Button>
        </Card.Actions>
      </Card>

      <Card style={styles.card}>
        <Card.Title title="Today's Activities" />
        <Card.Content>
          {todayActivities.length === 0 ? (
            <Text>No activities logged yet today</Text>
          ) : (
            todayActivities.map((activity) => (
              <View key={activity.id} style={styles.activityItem}>
                <Text style={styles.activityCategory}>
                  {activity.activity_category}
                </Text>
                <Text style={styles.activityTime}>
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </Text>
              </View>
            ))
          )}
        </Card.Content>
        <Card.Actions>
          <Button onPress={() => navigation.navigate('ActivityLog')}>
            Log New Activity
          </Button>
        </Card.Actions>
      </Card>

      <Card style={styles.card}>
        <Card.Title title="Quick Stats" />
        <Card.Content>
          <Text>Activities today: {todayActivities.length}</Text>
          <Text>Total time tracked: {todayActivities.length * 30} minutes</Text>
        </Card.Content>
        <Card.Actions>
          <Button onPress={() => navigation.navigate('Analytics')}>
            View Analytics
          </Button>
        </Card.Actions>
      </Card>
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
  subtitle: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
  },
  card: {
    margin: 16,
    marginBottom: 0,
  },
  activityItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  activityCategory: {
    fontSize: 16,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  activityTime: {
    fontSize: 14,
    color: '#666',
  },
});
