import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import random

# Bus route information
ROUTE_STOPS = [
    {"name": "Colombo Fort", "lat": 6.9271, "lon": 79.8612, "avg_passengers": 35},
    {"name": "Pettah", "lat": 6.9356, "lon": 79.8487, "avg_passengers": 42},
    {"name": "Maradana", "lat": 6.9287, "lon": 79.8631, "avg_passengers": 38},
    {"name": "Borella", "lat": 6.9146, "lon": 79.8779, "avg_passengers": 30},
    {"name": "Narahenpita", "lat": 6.9015, "lon": 79.8772, "avg_passengers": 25},
    {"name": "Nugegoda", "lat": 6.8649, "lon": 79.8997, "avg_passengers": 15}
]

# Constants from the Arduino code
MAX_CAPACITY = 50
NORMAL_THRESHOLD = 0.4  # <40% is undercrowded
YELLOW_THRESHOLD = 0.6  # 60% nearly full
RED_THRESHOLD = 0.8     # 80% overcrowded

def get_status(occupancy_percent):
    """Determine bus status based on occupancy percentage"""
    if occupancy_percent < NORMAL_THRESHOLD * 100:
        return "UNDERCROWDED"
    elif occupancy_percent < YELLOW_THRESHOLD * 100:
        return "NORMAL"
    elif occupancy_percent < RED_THRESHOLD * 100:
        return "NEARLY_FULL"
    else:
        return "OVERCROWDED"

def generate_passenger_pattern(hour):
    """Generate realistic passenger patterns based on time of day"""
    # Morning rush: 7-9 AM
    if 7 <= hour <= 9:
        base_multiplier = 1.5
    # Evening rush: 5-7 PM
    elif 17 <= hour <= 19:
        base_multiplier = 1.4
    # Mid-day: 11 AM - 2 PM
    elif 11 <= hour <= 14:
        base_multiplier = 0.8
    # Early morning: 5-7 AM
    elif 5 <= hour <= 7:
        base_multiplier = 0.6
    # Late evening: 8-10 PM
    elif 20 <= hour <= 22:
        base_multiplier = 0.4
    else:
        base_multiplier = 0.3
    
    return base_multiplier

def simulate_sensor_readings(actual_count):
    """Simulate IR and camera sensor readings with realistic variations"""
    # IR sensor is generally accurate but might miss in crowded conditions
    if actual_count > 40:
        ir_variation = random.randint(-2, 1)
    else:
        ir_variation = random.randint(-1, 1)
    
    ir_count = max(0, min(MAX_CAPACITY, actual_count + ir_variation))
    
    # Camera accuracy varies based on crowding
    if actual_count > 40:
        camera_accuracy = random.uniform(0.85, 0.95)
    else:
        camera_accuracy = random.uniform(0.90, 0.98)
    
    camera_variation = int(actual_count * (1 - camera_accuracy))
    camera_count = max(0, min(MAX_CAPACITY + 3, actual_count + random.randint(-camera_variation, camera_variation + 2)))
    
    # Sensor fusion (70% camera, 30% IR when crowded)
    if abs(camera_count - ir_count) <= 2:
        validated_count = round(0.7 * camera_count + 0.3 * ir_count)
    elif actual_count > 30:
        validated_count = camera_count
    else:
        validated_count = ir_count
    
    validated_count = max(0, min(MAX_CAPACITY, validated_count))
    
    return ir_count, camera_count, validated_count

def generate_bus_data():
    """Generate realistic bus operation data for a full day"""
    data = []
    
    # Simulate one full day of operation (5 AM to 11 PM)
    start_time = datetime(2024, 1, 15, 5, 0, 0)  # Monday
    
    # Multiple trips throughout the day
    current_time = start_time
    trip_number = 1
    
    while current_time.hour < 23:
        # One complete trip (forward and backward)
        for direction in ['Forward', 'Backward']:
            stops = ROUTE_STOPS if direction == 'Forward' else ROUTE_STOPS[::-1]
            
            # Initialize passenger count for this trip
            if direction == 'Forward':
                passenger_count = random.randint(5, 15)  # Start with some passengers
            
            for stop_idx, stop in enumerate(stops):
                # Time at stop
                stop_arrival = current_time
                
                # Passenger flow based on stop and time
                hour_multiplier = generate_passenger_pattern(current_time.hour)
                base_passengers = max(1, int(stop['avg_passengers'] * hour_multiplier))
                
                # Boarding and alighting
                if stop_idx == 0:  # First stop
                    boarding = max(1, min(random.randint(base_passengers - 5, base_passengers + 5), MAX_CAPACITY - passenger_count))
                    alighting = 0
                elif stop_idx == len(stops) - 1:  # Last stop
                    boarding = 0
                    alighting = passenger_count
                else:
                    # Ensure we have passengers before trying to alight
                    if passenger_count > 2:
                        alighting = random.randint(2, min(10, passenger_count))
                    elif passenger_count > 0:
                        alighting = random.randint(0, passenger_count)
                    else:
                        alighting = 0
                    # Calculate available space
                    available_space = MAX_CAPACITY - passenger_count + alighting
                    # Calculate boarding range
                    min_boarding = max(0, base_passengers - 8)
                    max_boarding = min(base_passengers + 8, available_space)
                    
                    # Ensure valid range
                    if min_boarding > max_boarding:
                        boarding = min(available_space, base_passengers)
                    else:
                        boarding = random.randint(min_boarding, max_boarding)
                
                passenger_count = passenger_count - alighting + boarding
                passenger_count = max(0, min(MAX_CAPACITY, passenger_count))
                
                # Simulate sensor readings
                ir_count, camera_count, validated_count = simulate_sensor_readings(passenger_count)
                
                # Calculate occupancy and status
                occupancy_percent = (validated_count / MAX_CAPACITY) * 100
                status = get_status(occupancy_percent)
                
                # Determine if alert triggered
                alert_triggered = "Yes" if status == "OVERCROWDED" else "No"
                
                # Record data
                data.append({
                    'timestamp': stop_arrival,
                    'trip_number': trip_number,
                    'direction': direction,
                    'bus_id': 'BUS-138-CMB',
                    'stop_name': stop['name'],
                    'latitude': stop['lat'],
                    'longitude': stop['lon'],
                    'boarding': boarding,
                    'alighting': alighting,
                    'ir_sensor_count': ir_count,
                    'camera_count': camera_count,
                    'validated_count': validated_count,
                    'actual_count': passenger_count,
                    'occupancy_percent': round(occupancy_percent, 2),
                    'status': status,
                    'alert_triggered': alert_triggered,
                    'sensor_mismatch': abs(camera_count - ir_count)
                })
                
                # Move to next stop (3-5 minutes travel time)
                current_time += timedelta(minutes=random.randint(3, 5))
            
            # Break between trips (5-10 minutes)
            current_time += timedelta(minutes=random.randint(5, 10))
        
        trip_number += 1
    
    return pd.DataFrame(data)

def create_visualizations(df):
    """Create all required visualizations for the evaluation section"""
    
    # Set style - handle different matplotlib versions
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except:
        try:
            plt.style.use('seaborn-darkgrid')
        except:
            plt.style.use('default')
    
    sns.set_palette("husl")
    
    # 1. Passenger Count Over Time (Line Graph)
    plt.figure(figsize=(14, 6))
    hourly_avg = df.groupby('hour')['validated_count'].mean()
    
    plt.subplot(1, 2, 1)
    plt.plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2, markersize=8)
    plt.fill_between(hourly_avg.index, hourly_avg.values, alpha=0.3)
    plt.axhline(y=MAX_CAPACITY * RED_THRESHOLD, color='red', linestyle='--', label='Overcrowded Threshold')
    plt.axhline(y=MAX_CAPACITY * YELLOW_THRESHOLD, color='orange', linestyle='--', label='Nearly Full Threshold')
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Passenger Count')
    plt.title('Average Passenger Count Throughout the Day')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Peak Hours Analysis
    plt.subplot(1, 2, 2)
    peak_hours = df[df['occupancy_percent'] > 80].groupby('hour').size()
    if not peak_hours.empty:
        plt.bar(peak_hours.index, peak_hours.values, color='red', alpha=0.7)
        plt.xlabel('Hour of Day')
        plt.ylabel('Number of Overcrowding Events')
        plt.title('Overcrowding Events by Hour')
    
    plt.tight_layout()
    plt.savefig('passenger_count_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Bus Stop Crowding Heatmap
    plt.figure(figsize=(12, 8))
    pivot_data = df.pivot_table(values='occupancy_percent', index='stop_name', columns='hour', aggfunc='mean')
    
    # Reorder stops in route order
    stop_order = [stop['name'] for stop in ROUTE_STOPS]
    pivot_data = pivot_data.reindex(stop_order)
    
    sns.heatmap(pivot_data, cmap='YlOrRd', annot=True, fmt='.0f', cbar_kws={'label': 'Occupancy %'})
    plt.title('Average Occupancy Percentage by Stop and Hour')
    plt.xlabel('Hour of Day')
    plt.ylabel('Bus Stop')
    plt.tight_layout()
    plt.savefig('stop_crowding_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Status Distribution (Pie Chart)
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    status_counts = df['status'].value_counts()
    colors = {'UNDERCROWDED': '#90EE90', 'NORMAL': '#87CEEB', 'NEARLY_FULL': '#FFD700', 'OVERCROWDED': '#FF6B6B'}
    plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', 
            colors=[colors[status] for status in status_counts.index])
    plt.title('Distribution of Bus Status Throughout Day')
    
    # 5. Alert Analysis by Stop
    plt.subplot(1, 2, 2)
    alerts_by_stop = df[df['alert_triggered'] == 'Yes'].groupby('stop_name').size()
    if not alerts_by_stop.empty:
        alerts_by_stop = alerts_by_stop.reindex(stop_order, fill_value=0)
        plt.bar(range(len(alerts_by_stop)), alerts_by_stop.values, 
                color=['red' if x > 0 else 'green' for x in alerts_by_stop.values])
        plt.xticks(range(len(alerts_by_stop)), alerts_by_stop.index, rotation=45, ha='right')
        plt.xlabel('Bus Stop')
        plt.ylabel('Number of Alerts')
        plt.title('Overcrowding Alerts by Stop')
    
    plt.tight_layout()
    plt.savefig('status_and_alerts.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. Sensor Accuracy Analysis
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.scatter(df['ir_sensor_count'], df['camera_count'], alpha=0.5, s=30)
    plt.plot([0, MAX_CAPACITY], [0, MAX_CAPACITY], 'r--', label='Perfect Agreement')
    plt.xlabel('IR Sensor Count')
    plt.ylabel('Camera Count')
    plt.title('IR Sensor vs Camera Count Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    mismatch_by_occupancy = df.groupby(pd.cut(df['occupancy_percent'], 
                                              bins=[0, 40, 60, 80, 100]))['sensor_mismatch'].mean()
    mismatch_by_occupancy.plot(kind='bar', color='orange')
    plt.xlabel('Occupancy Percentage Range')
    plt.ylabel('Average Sensor Mismatch')
    plt.title('Sensor Mismatch vs Occupancy Level')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('sensor_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def calculate_kpis(df):
    """Calculate and display Key Performance Indicators"""
    print("\n=== KEY PERFORMANCE INDICATORS ===\n")
    
    # 1. Maximum capacity utilization
    max_utilization = df['occupancy_percent'].max()
    print(f"1. Maximum Capacity Utilization: {max_utilization:.1f}%")
    
    # 2. Percentage of time overcrowded
    overcrowded_percentage = (df['status'] == 'OVERCROWDED').sum() / len(df) * 100
    print(f"2. Percentage of Journey Time Overcrowded: {overcrowded_percentage:.1f}%")
    
    # 3. Number of alerts
    total_alerts = (df['alert_triggered'] == 'Yes').sum()
    print(f"3. Total Overcrowding Alerts Triggered: {total_alerts}")
    
    # 4. Most crowded stops
    avg_by_stop = df.groupby('stop_name')['occupancy_percent'].mean().sort_values(ascending=False)
    print(f"4. Most Crowded Stop: {avg_by_stop.index[0]} ({avg_by_stop.values[0]:.1f}% average occupancy)")
    
    # 5. Peak hours
    hourly_avg = df.groupby('hour')['occupancy_percent'].mean()
    peak_hour = hourly_avg.idxmax()
    print(f"5. Peak Hour: {peak_hour}:00 ({hourly_avg[peak_hour]:.1f}% average occupancy)")
    
    # 6. Sensor accuracy
    avg_mismatch = df['sensor_mismatch'].mean()
    print(f"6. Average Sensor Mismatch: {avg_mismatch:.2f} passengers")
    
    # Save KPIs to file
    with open('kpi_summary.txt', 'w', encoding='utf-8') as f:
        f.write("KEY PERFORMANCE INDICATORS - Smart Bus Overcrowding Detection System\n")
        f.write("="*60 + "\n\n")
        f.write(f"1. Maximum Capacity Utilization: {max_utilization:.1f}%\n")
        f.write(f"2. Percentage of Journey Time Overcrowded: {overcrowded_percentage:.1f}%\n")
        f.write(f"3. Total Overcrowding Alerts Triggered: {total_alerts}\n")
        f.write(f"4. Most Crowded Stop: {avg_by_stop.index[0]} ({avg_by_stop.values[0]:.1f}% average occupancy)\n")
        f.write(f"5. Peak Hour: {peak_hour}:00 ({hourly_avg[peak_hour]:.1f}% average occupancy)\n")
        f.write(f"6. Average Sensor Mismatch: {avg_mismatch:.2f} passengers\n")

if __name__ == "__main__":
    print("Generating bus operation data...")
    df = generate_bus_data()
    
    # Add hour column before saving
    df['hour'] = df['timestamp'].dt.hour
    
    # Save to CSV
    df.to_csv('bus_overcrowding_data.csv', index=False)
    print(f"Data saved to 'bus_overcrowding_data.csv' ({len(df)} records)")
    
    # Calculate KPIs
    calculate_kpis(df)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(df)
    print("Visualizations saved:")
    print("- passenger_count_analysis.png")
    print("- stop_crowding_heatmap.png")
    print("- status_and_alerts.png")
    print("- sensor_analysis.png")
    print("- kpi_summary.txt")