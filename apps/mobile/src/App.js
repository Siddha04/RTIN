import React, { useEffect, useState } from 'react';
import { Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';

const API = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export default function App() {
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState('inspector@inspect-ai.local');
  const [password, setPassword] = useState('Inspector@123');
  const [loggingIn, setLoggingIn] = useState(false);

  const [inspections, setInspections] = useState([]);
  const [selectedInsp, setSelectedInsp] = useState(null);
  const [location, setLocation] = useState(null);
  const [notes, setNotes] = useState('');
  const [checklist, setChecklist] = useState({
    attendance_verified: true,
    infrastructure_ok: true,
    beneficiary_count_validated: true,
    safety_norms_passed: true
  });
  const [queued, setQueued] = useState([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem('mobile_token').then((t) => setToken(t));
    AsyncStorage.getItem('offline_queue').then((q) => {
      if (q) setQueued(JSON.parse(q));
    });
  }, []);

  useEffect(() => {
    if (token) {
      fetchInspections();
    }
  }, [token]);

  const handleLogin = async () => {
    setLoggingIn(true);
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      await AsyncStorage.setItem('mobile_token', data.access_token);
      setToken(data.access_token);
    } catch (err) {
      Alert.alert('Authentication Error', err.message);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('mobile_token');
    setToken(null);
    setInspections([]);
    setSelectedInsp(null);
  };

  const fetchInspections = async () => {
    try {
      const res = await fetch(`${API}/api/inspections`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setInspections(data);
      }
    } catch (_) {
      // Offline fallback: keep existing list
    }
  };

  const startInspection = async (insp) => {
    setSelectedInsp(insp);
    const perm = await Location.requestForegroundPermissionsAsync();
    if (perm.status === 'granted') {
      try {
        const pos = await Location.getCurrentPositionAsync({});
        setLocation(pos.coords);
      } catch (_) {
        setLocation({ latitude: 11.6643, longitude: 78.1460 });
      }
    } else {
      setLocation({ latitude: 11.6643, longitude: 78.1460 });
    }
  };

  const submitInspection = async () => {
    const payload = {
      inspection_id: selectedInsp.id,
      institution_id: selectedInsp.institution_id,
      notes,
      checklist,
      latitude: location ? location.latitude : 11.6643,
      longitude: location ? location.longitude : 78.1460,
      timestamp: new Date().toISOString()
    };

    // Try online sync first
    try {
      const res = await fetch(`${API}/api/inspections/${selectedInsp.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          status: 'completed',
          notes: payload.notes,
          checklist_data: payload.checklist
        })
      });

      if (res.ok) {
        Alert.alert('Inspection Submitted', 'Inspection record successfully synchronized with central command server.');
        setSelectedInsp(null);
        setNotes('');
        fetchInspections();
        return;
      }
    } catch (_) {
      // Failed online call -> queue offline
    }

    // Queue offline
    const updatedQueue = [...queued, payload];
    setQueued(updatedQueue);
    await AsyncStorage.setItem('offline_queue', JSON.stringify(updatedQueue));
    setSelectedInsp(null);
    setNotes('');
    Alert.alert('Queued Offline', 'Network unavailable. Inspection saved locally in offline queue.');
  };

  const syncQueue = async () => {
    if (queued.length === 0) {
      Alert.alert('Sync Status', 'Offline queue is empty.');
      return;
    }
    setSyncing(true);
    let remaining = [...queued];
    let syncedCount = 0;

    for (const item of queued) {
      try {
        const res = await fetch(`${API}/api/inspections/${item.inspection_id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            status: 'completed',
            notes: item.notes,
            checklist_data: item.checklist
          })
        });

        if (res.ok) {
          remaining = remaining.filter((q) => q.inspection_id !== item.inspection_id);
          syncedCount++;
        }
      } catch (_) {}
    }

    setQueued(remaining);
    await AsyncStorage.setItem('offline_queue', JSON.stringify(remaining));
    setSyncing(false);
    Alert.alert('Sync Complete', `Synchronized ${syncedCount} queued records with server.`);
    fetchInspections();
  };

  if (!token) {
    return (
      <SafeAreaView style={styles.root}>
        <View style={styles.header}>
          <Text style={styles.logo}>INSPECT-AI MOBILE</Text>
          <Text style={styles.sync}>FIELD APP</Text>
        </View>

        <View style={styles.body}>
          <Text style={styles.h1}>Inspector Sign In</Text>
          <Text style={styles.caption}>Authenticate with your officer credentials.</Text>

          <Text style={styles.label}>Email Address</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
          />

          <Text style={styles.label}>Password</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Pressable style={styles.button} onPress={handleLogin} disabled={loggingIn}>
            {loggingIn ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.buttonText}>Sign In as Field Inspector</Text>
            )}
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.logo}>INSPECT-AI</Text>
        <Pressable onPress={syncQueue}>
          <Text style={styles.sync}>
            ● {queued.length > 0 ? `${queued.length} queued (Tap to Sync)` : 'Synced'}
          </Text>
        </Pressable>
      </View>

      {selectedInsp ? (
        <ScrollView style={styles.body}>
          <Text style={styles.h1}>Field Inspection Form</Text>
          <Text style={styles.name}>{selectedInsp.institution_name}</Text>
          <Text style={styles.meta}>ID: {selectedInsp.id} · Inspector: {selectedInsp.inspector}</Text>

          <View style={styles.verify}>
            <Text style={styles.white}>Evidence & Integrity Metadata</Text>
            <Text style={styles.light}>
              {location ? `✓ GPS: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}` : '○ Acquiring GPS...'}
            </Text>
            <Text style={styles.light}>✓ Timestamp: {new Date().toLocaleTimeString()}</Text>
            <Text style={styles.light}>✓ Officer Session Active</Text>
          </View>

          <Text style={styles.label}>Inspection Checklist</Text>
          <Pressable
            style={styles.checkItem}
            onPress={() => setChecklist({ ...checklist, attendance_verified: !checklist.attendance_verified })}
          >
            <Text style={styles.checkText}>
              {checklist.attendance_verified ? '☑' : '☐'} Physical Attendance Verified
            </Text>
          </Pressable>

          <Pressable
            style={styles.checkItem}
            onPress={() => setChecklist({ ...checklist, infrastructure_ok: !checklist.infrastructure_ok })}
          >
            <Text style={styles.checkText}>
              {checklist.infrastructure_ok ? '☑' : '☐'} Infrastructure Safety Norms OK
            </Text>
          </Pressable>

          <Pressable
            style={styles.checkItem}
            onPress={() => setChecklist({ ...checklist, beneficiary_count_validated: !checklist.beneficiary_count_validated })}
          >
            <Text style={styles.checkText}>
              {checklist.beneficiary_count_validated ? '☑' : '☐'} Beneficiary Headcount Validated
            </Text>
          </Pressable>

          <Text style={[styles.label, { marginTop: 15 }]}>Field Auditor Notes</Text>
          <TextInput
            multiline
            value={notes}
            onChangeText={setNotes}
            placeholder="Record detailed field findings..."
            style={[styles.input, { height: 100 }]}
          />

          <View style={{ flexDirection: 'row', gap: 10, marginTop: 15 }}>
            <Pressable style={[styles.button, { flex: 1, backgroundColor: '#8295A5' }]} onPress={() => setSelectedInsp(null)}>
              <Text style={styles.buttonText}>Cancel</Text>
            </Pressable>
            <Pressable style={[styles.button, { flex: 1 }]} onPress={submitInspection}>
              <Text style={styles.buttonText}>Complete Inspection</Text>
            </Pressable>
          </View>
        </ScrollView>
      ) : (
        <ScrollView style={styles.body}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View>
              <Text style={styles.h1}>My Inspections</Text>
              <Text style={styles.caption}>Assigned tasks prioritized by AI engine.</Text>
            </View>
            <Pressable onPress={handleLogout}>
              <Text style={{ color: '#A33731', fontSize: 11, fontWeight: 'bold' }}>Sign Out</Text>
            </Pressable>
          </View>

          {inspections.map((insp) => (
            <Pressable key={insp.id} onPress={() => startInspection(insp)} style={styles.card}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                <Text style={styles.badge}>{String(insp.status).toUpperCase()}</Text>
                {insp.priority && <Text style={[styles.badge, { backgroundColor: '#FDE8E6', color: '#A33731' }]}>PRIORITY</Text>}
              </View>
              <Text style={styles.name}>{insp.institution_name}</Text>
              <Text style={styles.meta}>{insp.id} · {insp.district}</Text>
              <Pressable style={styles.button} onPress={() => startInspection(insp)}>
                <Text style={styles.buttonText}>Start Inspection</Text>
              </Pressable>
            </Pressable>
          ))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F3F7FA' },
  header: { backgroundColor: '#0C3558', padding: 18, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  logo: { color: '#FFF', fontWeight: '800', letterSpacing: 2, fontSize: 16 },
  sync: { color: '#BFE0D5', fontSize: 11, fontWeight: 'bold' },
  body: { padding: 18 },
  h1: { fontSize: 22, fontWeight: '800', color: '#17354D', marginBottom: 4 },
  caption: { fontSize: 12, color: '#778C9E', marginBottom: 16 },
  card: { backgroundColor: '#FFF', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#DCE6EC', marginBottom: 12 },
  badge: { alignSelf: 'flex-start', backgroundColor: '#E8F3FA', color: '#145980', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, fontSize: 9, fontWeight: '800' },
  name: { fontSize: 15, fontWeight: '800', color: '#213F54', marginTop: 8 },
  meta: { fontSize: 11, color: '#8396A5', marginTop: 2 },
  button: { backgroundColor: '#0E7F7A', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  buttonText: { color: '#FFF', fontWeight: '800', fontSize: 12 },
  verify: { backgroundColor: '#0E3D5C', padding: 14, borderRadius: 10, marginVertical: 14 },
  white: { color: '#FFF', fontWeight: '800', marginBottom: 6, fontSize: 13 },
  light: { color: '#C9DCE9', fontSize: 12, paddingVertical: 2 },
  label: { fontSize: 12, fontWeight: '800', color: '#536B7D', marginBottom: 6 },
  input: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#D7E1E8', borderRadius: 8, padding: 10, marginBottom: 12, fontSize: 14 },
  checkItem: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#D7E1E8', padding: 12, borderRadius: 8, marginBottom: 6 },
  checkText: { fontSize: 13, color: '#17354D', fontWeight: '600' }
});
