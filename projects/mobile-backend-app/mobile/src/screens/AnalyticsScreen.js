import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Dimensions } from 'react-native';
import { Title, Card, Text, SegmentedButtons } from 'react-native-paper';
import { PieChart, BarChart } from 'react-native-chart-kit';
import { activityAPI } from '../services/api';

const screenWidth = Dimensions.get('window').width;

export default function AnalyticsScreen() {
  const [period, setPeriod] = useState('day');
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const now = new Date();
      let startDate;

      if (period === 'day') {
        startDate = new Date(now.setHours(0, 0, 0, 0));
      } else if (period === 'week') {
        startDate = new Date(now.setDate(now.getDate() - 7));
      } else {
        startDate = new Date(now.setDate(now.getDate() - 30));
      }

      const response = await activityAPI.getAll({
        start_date: startDate.toISOString(),
        page_size: 100,
      });

      setActivities(response.data.items);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryDistribution = () => {
    const distribution = {};

    activities.forEach((activity) => {
      const category = activity.activity_category;
      if (!distribution[category]) {
        distribution[category] = 0;
      }
      distribution[category] += activity.duration_minutes || 30;
    });

    return Object.entries(distribution).map(([name, minutes], index) => ({
      name,
      minutes,
      color: `hsl(${(index * 360) / Object.keys(distribution).length}, 70%, 50%)`,
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    }));
  };

  const getProductivityData = () => {
    if (activities.length === 0) return null;

    const productivityByDay = {};

    activities.forEach((activity) => {
      if (activity.productivity_rating) {
        const date = new Date(activity.timestamp).toLocaleDateString();
        if (!productivityByDay[date]) {
          productivityByDay[date] = { total: 0, count: 0 };
        }
        productivityByDay[date].total += activity.productivity_rating;
        productivityByDay[date].count += 1;
      }
    });

    const labels = Object.keys(productivityByDay).slice(-7);
    const data = labels.map((date) => {
      const avg = productivityByDay[date].total / productivityByDay[date].count;
      return avg;
    });

    return {
      labels,
      datasets: [{ data }],
    };
  };

  const categoryData = getCategoryDistribution();
  const productivityData = getProductivityData();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>Analytics</Title>
      </View>

      <Card style={styles.card}>
        <Card.Content>
          <SegmentedButtons
            value={period}
            onValueChange={setPeriod}
            buttons={[
              { value: 'day', label: 'Today' },
              { value: 'week', label: 'Week' },
              { value: 'month', label: 'Month' },
            ]}
          />
        </Card.Content>
      </Card>

      {activities.length === 0 ? (
        <Card style={styles.card}>
          <Card.Content>
            <Text>No activities in this period</Text>
          </Card.Content>
        </Card>
      ) : (
        <>
          <Card style={styles.card}>
            <Card.Title title="Time Distribution by Category" />
            <Card.Content>
              {categoryData.length > 0 && (
                <PieChart
                  data={categoryData}
                  width={screenWidth - 64}
                  height={220}
                  chartConfig={{
                    color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                  }}
                  accessor="minutes"
                  backgroundColor="transparent"
                  paddingLeft="15"
                  absolute
                />
              )}
            </Card.Content>
          </Card>

          {productivityData && (
            <Card style={styles.card}>
              <Card.Title title="Productivity Trend" />
              <Card.Content>
                <BarChart
                  data={productivityData}
                  width={screenWidth - 64}
                  height={220}
                  chartConfig={{
                    backgroundColor: '#ffffff',
                    backgroundGradientFrom: '#ffffff',
                    backgroundGradientTo: '#ffffff',
                    decimalPlaces: 1,
                    color: (opacity = 1) => `rgba(98, 0, 238, ${opacity})`,
                    style: {
                      borderRadius: 16,
                    },
                  }}
                  style={{
                    marginVertical: 8,
                    borderRadius: 16,
                  }}
                />
              </Card.Content>
            </Card>
          )}

          <Card style={styles.card}>
            <Card.Title title="Summary" />
            <Card.Content>
              <Text>Total activities: {activities.length}</Text>
              <Text>Total time tracked: {activities.length * 30} minutes</Text>
              <Text>
                Average productivity:{' '}
                {(
                  activities.reduce(
                    (sum, a) => sum + (a.productivity_rating || 0),
                    0
                  ) / activities.length
                ).toFixed(1)}
                /5
              </Text>
            </Card.Content>
          </Card>
        </>
      )}
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
  card: {
    margin: 16,
    marginBottom: 0,
  },
});
