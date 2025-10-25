import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { TextInput, Button, Title, SegmentedButtons, Text, Chip } from 'react-native-paper';
import * as Location from 'expo-location';
import { activityAPI } from '../services/api';

const ACTIVITY_CATEGORIES = [
  'work',
  'study',
  'exercise',
  'leisure',
  'social',
  'sleep',
  'meal',
  'commute',
  'other',
];

const MOODS = ['happy', 'neutral', 'sad', 'stressed', 'energetic', 'tired'];

export default function ActivityLogScreen({ navigation }) {
  const [category, setCategory] = useState('');
  const [detail, setDetail] = useState('');
  const [energyLevel, setEnergyLevel] = useState('3');
  const [productivityRating, setProductivityRating] = useState('3');
  const [mood, setMood] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!category) {
      Alert.alert('Error', 'Please select an activity category');
      return;
    }

    setLoading(true);

    try {
      // Get location
      let locationData = null;
      const { status } = await Location.requestForegroundPermissionsAsync();

      if (status === 'granted') {
        try {
          const location = await Location.getCurrentPositionAsync({});
          locationData = {
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
            accuracy: location.coords.accuracy,
          };
        } catch (error) {
          console.error('Failed to get location:', error);
        }
      }

      // Prepare activity data
      const activityData = {
        timestamp: new Date().toISOString(),
        activity_category: category,
        activity_detail: detail || null,
        duration_minutes: 30,
        energy_level: parseInt(energyLevel),
        productivity_rating: parseInt(productivityRating),
        mood: mood || null,
        notes: notes || null,
        location_context: locationData,
      };

      await activityAPI.create(activityData);

      Alert.alert('Success', 'Activity logged successfully!');

      // Reset form
      setCategory('');
      setDetail('');
      setEnergyLevel('3');
      setProductivityRating('3');
      setMood('');
      setNotes('');

      // Navigate to home
      navigation.navigate('Home');
    } catch (error) {
      console.error('Failed to log activity:', error);
      Alert.alert('Error', 'Failed to log activity. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Title style={styles.title}>Log Your Activity</Title>
        <Text style={styles.subtitle}>What have you been doing?</Text>

        <Text style={styles.label}>Activity Category *</Text>
        <View style={styles.chipContainer}>
          {ACTIVITY_CATEGORIES.map((cat) => (
            <Chip
              key={cat}
              selected={category === cat}
              onPress={() => setCategory(cat)}
              style={styles.chip}
            >
              {cat}
            </Chip>
          ))}
        </View>

        <TextInput
          label="Activity Detail (optional)"
          value={detail}
          onChangeText={setDetail}
          mode="outlined"
          style={styles.input}
          placeholder="e.g., Meeting with team, Reading book, etc."
        />

        <Text style={styles.label}>Energy Level</Text>
        <SegmentedButtons
          value={energyLevel}
          onValueChange={setEnergyLevel}
          buttons={[
            { value: '1', label: '1' },
            { value: '2', label: '2' },
            { value: '3', label: '3' },
            { value: '4', label: '4' },
            { value: '5', label: '5' },
          ]}
          style={styles.segmented}
        />

        <Text style={styles.label}>Productivity</Text>
        <SegmentedButtons
          value={productivityRating}
          onValueChange={setProductivityRating}
          buttons={[
            { value: '1', label: '1' },
            { value: '2', label: '2' },
            { value: '3', label: '3' },
            { value: '4', label: '4' },
            { value: '5', label: '5' },
          ]}
          style={styles.segmented}
        />

        <Text style={styles.label}>Mood</Text>
        <View style={styles.chipContainer}>
          {MOODS.map((m) => (
            <Chip
              key={m}
              selected={mood === m}
              onPress={() => setMood(m)}
              style={styles.chip}
            >
              {m}
            </Chip>
          ))}
        </View>

        <TextInput
          label="Notes (optional)"
          value={notes}
          onChangeText={setNotes}
          mode="outlined"
          multiline
          numberOfLines={3}
          style={styles.input}
        />

        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={loading}
          disabled={loading || !category}
          style={styles.button}
        >
          Log Activity
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  label: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 16,
    marginBottom: 8,
  },
  input: {
    marginBottom: 16,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
  },
  segmented: {
    marginBottom: 16,
  },
  button: {
    marginTop: 24,
    marginBottom: 40,
    paddingVertical: 8,
  },
});
