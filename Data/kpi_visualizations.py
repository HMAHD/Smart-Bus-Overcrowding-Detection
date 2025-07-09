import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates

# Create KPI folder if it doesn't exist
if not os.path.exists('KPI'):
    os.makedirs('KPI')

def setup_plot_style():
    """Set up consistent plot styling"""
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        try:
            plt.style.use('seaborn-whitegrid')
        except:
            plt.style.use('default')
    
    # Set default figure parameters
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10

def create_line_graph_passenger_count(df):
    """1. Line Graph - Passenger Count Over Time"""
    plt.figure(figsize=(14, 8))
    
    # Calculate hourly averages
    hourly_avg = df.groupby('hour').agg({
        'validated_count': 'mean',
        'ir_sensor_count': 'mean',
        'camera_count': 'mean'
    })
    
    # Main plot
    plt.plot(hourly_avg.index, hourly_avg['validated_count'], 
             marker='o', linewidth=3, markersize=8, label='Validated Count', color='#2E86AB')
    plt.plot(hourly_avg.index, hourly_avg['ir_sensor_count'], 
             linestyle='--', alpha=0.7, label='IR Sensor', color='#A23B72')
    plt.plot(hourly_avg.index, hourly_avg['camera_count'], 
             linestyle='--', alpha=0.7, label='Camera', color='#F18F01')
    
    # Add threshold lines
    plt.axhline(y=30, color='orange', linestyle=':', linewidth=2, label='60% Capacity (Nearly Full)')
    plt.axhline(y=40, color='red', linestyle=':', linewidth=2, label='80% Capacity (Overcrowded)')
    
    # Fill areas
    plt.fill_between(hourly_avg.index, 0, 30, alpha=0.1, color='green')
    plt.fill_between(hourly_avg.index, 30, 40, alpha=0.1, color='orange')
    plt.fill_between(hourly_avg.index, 40, 50, alpha=0.1, color='red')
    
    plt.xlabel('Hour of Day')
    plt.ylabel('Average Passenger Count')
    plt.title('Average Passenger Count Throughout the Day - Route 138')
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 24))
    
    # Add annotations for peak hours
    peak_hour = hourly_avg['validated_count'].idxmax()
    peak_value = hourly_avg['validated_count'].max()
    plt.annotate(f'Peak: {peak_value:.0f} passengers', 
                xy=(peak_hour, peak_value), 
                xytext=(peak_hour+2, peak_value+3),
                arrowprops=dict(arrowstyle='->', color='black', alpha=0.7),
                fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('KPI/1_passenger_count_over_time.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_heatmap_crowding_levels(df):
    """2. Heat Map - Crowding Levels by Stop and Time"""
    plt.figure(figsize=(14, 8))
    
    # Create pivot table
    pivot_data = df.pivot_table(values='occupancy_percent', 
                                index='stop_name', 
                                columns='hour', 
                                aggfunc='mean')
    
    # Define stop order
    stop_order = ['Colombo Fort', 'Pettah', 'Maradana', 'Borella', 'Narahenpita', 'Nugegoda']
    pivot_data = pivot_data.reindex(stop_order)
    
    # Create custom colormap
    colors = ['#2E7D32', '#43A047', '#66BB6A', '#FDD835', '#FFB300', '#FF6F00', '#E65100', '#BF360C']
    n_bins = 100
    cmap = sns.blend_palette(colors, n_colors=n_bins, as_cmap=True)
    
    # Create heatmap with annotations
    ax = sns.heatmap(pivot_data, 
                     cmap=cmap, 
                     annot=True, 
                     fmt='.0f', 
                     cbar_kws={'label': 'Occupancy Percentage (%)'}, 
                     linewidths=0.5,
                     vmin=0,
                     vmax=100)
    
    plt.title('Average Occupancy Percentage by Stop and Hour', fontsize=16, pad=20)
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Bus Stop', fontsize=12)
    
    # Rotate y-axis labels
    plt.yticks(rotation=0)
    
    # Add text to identify critical areas
    for i, stop in enumerate(stop_order):
        for j, hour in enumerate(pivot_data.columns):
            value = pivot_data.loc[stop, hour]
            if value >= 80:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor='red', lw=3))
    
    plt.tight_layout()
    plt.savefig('KPI/2_crowding_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_bar_chart_alerts(df):
    """3. Bar Chart - Alert Frequency by Location"""
    plt.figure(figsize=(12, 8))
    
    # Count alerts by stop
    alerts_by_stop = df[df['alert_triggered'] == 'Yes'].groupby('stop_name').size()
    
    # Define stop order and ensure all stops are included
    stop_order = ['Colombo Fort', 'Pettah', 'Maradana', 'Borella', 'Narahenpita', 'Nugegoda']
    alerts_by_stop = alerts_by_stop.reindex(stop_order, fill_value=0)
    
    # Create bar chart with gradient colors
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(alerts_by_stop)))
    bars = plt.bar(range(len(alerts_by_stop)), alerts_by_stop.values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, alerts_by_stop.values)):
        if value > 0:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{int(value)}', ha='center', va='bottom', fontweight='bold')
    
    plt.xticks(range(len(alerts_by_stop)), alerts_by_stop.index, rotation=45, ha='right')
    plt.xlabel('Bus Stop', fontsize=12)
    plt.ylabel('Number of Overcrowding Alerts', fontsize=12)
    plt.title('Overcrowding Alert Frequency by Bus Stop', fontsize=16, pad=20)
    plt.grid(axis='y', alpha=0.3)
    
    # Add a horizontal line for average
    avg_alerts = alerts_by_stop.mean()
    plt.axhline(y=avg_alerts, color='red', linestyle='--', alpha=0.7, label=f'Average: {avg_alerts:.1f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('KPI/3_alert_frequency_by_location.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_pie_chart_status(df):
    """4. Pie Chart - Distribution of Bus Status"""
    plt.figure(figsize=(10, 8))
    
    # Count status occurrences
    status_counts = df['status'].value_counts()
    
    # Define colors for each status
    colors = {
        'UNDERCROWDED': '#4CAF50',
        'NORMAL': '#2196F3', 
        'NEARLY_FULL': '#FF9800',
        'OVERCROWDED': '#F44336'
    }
    
    # Create pie chart
    wedges, texts, autotexts = plt.pie(status_counts.values, 
                                       labels=status_counts.index,
                                       colors=[colors.get(status, '#gray') for status in status_counts.index],
                                       autopct='%1.1f%%',
                                       startangle=90,
                                       explode=[0.05 if status == 'OVERCROWDED' else 0 for status in status_counts.index])
    
    # Enhance text
    for text in texts:
        text.set_fontsize(12)
        text.set_fontweight('bold')
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
    
    plt.title('Distribution of Bus Status Throughout Operation', fontsize=16, pad=20)
    
    # Add a legend with counts
    legend_labels = [f'{status}: {count} ({count/len(df)*100:.1f}%)' 
                    for status, count in status_counts.items()]
    plt.legend(wedges, legend_labels, title="Status", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    plt.savefig('KPI/4_status_distribution_pie.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_sensor_comparison_chart(df):
    """5. Additional Chart - Sensor Accuracy Comparison"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Scatter plot comparing sensors
    ax1.scatter(df['ir_sensor_count'], df['camera_count'], alpha=0.5, s=30, c=df['occupancy_percent'], cmap='viridis')
    ax1.plot([0, 50], [0, 50], 'r--', label='Perfect Agreement')
    ax1.set_xlabel('IR Sensor Count')
    ax1.set_ylabel('Camera Count')
    ax1.set_title('IR Sensor vs Camera Count Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Box plot of sensor mismatch by occupancy level
    df['occupancy_category'] = pd.cut(df['occupancy_percent'], 
                                      bins=[0, 40, 60, 80, 100],
                                      labels=['Low\n(0-40%)', 'Normal\n(40-60%)', 'High\n(60-80%)', 'Very High\n(80-100%)'])
    
    df.boxplot(column='sensor_mismatch', by='occupancy_category', ax=ax2)
    ax2.set_xlabel('Occupancy Level')
    ax2.set_ylabel('Sensor Mismatch (passengers)')
    ax2.set_title('Sensor Accuracy by Occupancy Level')
    plt.suptitle('')  # Remove default title
    
    plt.tight_layout()
    plt.savefig('KPI/5_sensor_accuracy_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_time_series_analysis(df):
    """6. Additional Chart - Time Series Analysis"""
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 1, figure=fig, hspace=0.3)
    
    # Convert timestamp to datetime if not already
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Top panel - Passenger count over full day
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(df['timestamp'], df['validated_count'], linewidth=1, color='#2E86AB', alpha=0.8)
    ax1.fill_between(df['timestamp'], df['validated_count'], alpha=0.3, color='#2E86AB')
    ax1.axhline(y=40, color='red', linestyle='--', alpha=0.7)
    ax1.set_ylabel('Passenger Count')
    ax1.set_title('Real-Time Passenger Count Throughout the Day', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # Middle panel - Boarding and alighting
    ax2 = fig.add_subplot(gs[1, :])
    ax2.bar(df['timestamp'], df['boarding'], width=0.01, alpha=0.7, label='Boarding', color='green')
    ax2.bar(df['timestamp'], -df['alighting'], width=0.01, alpha=0.7, label='Alighting', color='red')
    ax2.set_ylabel('Passengers')
    ax2.set_title('Boarding and Alighting Activity', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Bottom panel - Occupancy percentage
    ax3 = fig.add_subplot(gs[2, :])
    ax3.plot(df['timestamp'], df['occupancy_percent'], linewidth=2, color='#FF6B6B')
    ax3.fill_between(df['timestamp'], df['occupancy_percent'], 
                     where=(df['occupancy_percent'] >= 80), 
                     color='red', alpha=0.3, label='Overcrowded')
    ax3.fill_between(df['timestamp'], df['occupancy_percent'], 
                     where=(df['occupancy_percent'] >= 60) & (df['occupancy_percent'] < 80), 
                     color='orange', alpha=0.3, label='Nearly Full')
    ax3.set_ylabel('Occupancy %')
    ax3.set_xlabel('Time')
    ax3.set_title('Occupancy Percentage Over Time', fontsize=14)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Format x-axis for all subplots
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # Use constrained layout instead of tight_layout for GridSpec
    fig.set_constrained_layout(True)
    plt.savefig('KPI/6_time_series_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_stop_performance_dashboard(df):
    """7. Additional Chart - Stop Performance Dashboard"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Calculate stop metrics
    stop_metrics = df.groupby('stop_name').agg({
        'boarding': 'sum',
        'alighting': 'sum',
        'validated_count': 'mean',
        'alert_triggered': lambda x: (x == 'Yes').sum()
    })
    
    stop_order = ['Colombo Fort', 'Pettah', 'Maradana', 'Borella', 'Narahenpita', 'Nugegoda']
    stop_metrics = stop_metrics.reindex(stop_order)
    
    # 1. Total passenger flow by stop
    x = np.arange(len(stop_order))
    width = 0.35
    ax1.bar(x - width/2, stop_metrics['boarding'], width, label='Boarding', color='#2E7D32')
    ax1.bar(x + width/2, stop_metrics['alighting'], width, label='Alighting', color='#D32F2F')
    ax1.set_xlabel('Bus Stop')
    ax1.set_ylabel('Total Passengers')
    ax1.set_title('Total Passenger Flow by Stop')
    ax1.set_xticks(x)
    ax1.set_xticklabels(stop_order, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Average occupancy by stop
    bars = ax2.bar(stop_order, stop_metrics['validated_count'], 
                   color=['red' if x > 40 else 'orange' if x > 30 else 'green' 
                          for x in stop_metrics['validated_count']])
    ax2.set_xlabel('Bus Stop')
    ax2.set_ylabel('Average Passenger Count')
    ax2.set_title('Average Occupancy by Stop')
    ax2.axhline(y=40, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(y=30, color='orange', linestyle='--', alpha=0.5)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Passenger turnover rate
    turnover_rate = (stop_metrics['boarding'] + stop_metrics['alighting']) / 2
    ax3.plot(stop_order, turnover_rate, marker='o', linewidth=2, markersize=10, color='#1976D2')
    ax3.fill_between(range(len(stop_order)), turnover_rate, alpha=0.3, color='#1976D2')
    ax3.set_xlabel('Bus Stop')
    ax3.set_ylabel('Average Passenger Turnover')
    ax3.set_title('Passenger Turnover Rate by Stop')
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax3.grid(True, alpha=0.3)
    
    # 4. Alert rate by stop
    total_visits = df.groupby('stop_name').size().reindex(stop_order)
    alert_rate = (stop_metrics['alert_triggered'] / total_visits * 100).fillna(0)
    bars = ax4.bar(stop_order, alert_rate, color='#FF5252', edgecolor='black', linewidth=1)
    ax4.set_xlabel('Bus Stop')
    ax4.set_ylabel('Alert Rate (%)')
    ax4.set_title('Overcrowding Alert Rate by Stop')
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax4.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, value in zip(bars, alert_rate):
        if value > 0:
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('KPI/7_stop_performance_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_peak_hour_analysis(df):
    """8. Additional Chart - Peak Hour Analysis"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Group by hour
    hourly_stats = df.groupby('hour').agg({
        'validated_count': ['mean', 'max', 'min'],
        'boarding': 'sum',
        'alighting': 'sum',
        'alert_triggered': lambda x: (x == 'Yes').sum()
    })
    
    # Top panel - Passenger count statistics
    hours = hourly_stats.index
    mean_count = hourly_stats[('validated_count', 'mean')]
    max_count = hourly_stats[('validated_count', 'max')]
    min_count = hourly_stats[('validated_count', 'min')]
    
    ax1.plot(hours, mean_count, 'o-', linewidth=3, markersize=8, label='Average', color='#2E86AB')
    ax1.fill_between(hours, min_count, max_count, alpha=0.3, color='#2E86AB', label='Min-Max Range')
    
    # Mark peak hours
    morning_peak = (hours >= 7) & (hours <= 9)
    evening_peak = (hours >= 17) & (hours <= 19)
    ax1.fill_between(hours[morning_peak], 0, 50, alpha=0.2, color='red', label='Peak Hours')
    ax1.fill_between(hours[evening_peak], 0, 50, alpha=0.2, color='red')
    
    ax1.set_ylabel('Passenger Count')
    ax1.set_title('Hourly Passenger Count Statistics with Peak Hour Identification', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 52)
    
    # Bottom panel - Flow and alerts
    ax2_twin = ax2.twinx()
    
    # Passenger flow
    boarding = hourly_stats[('boarding', 'sum')]
    alighting = hourly_stats[('alighting', 'sum')]
    net_flow = boarding - alighting
    
    ax2.bar(hours - 0.2, boarding, width=0.4, label='Boarding', color='green', alpha=0.7)
    ax2.bar(hours + 0.2, alighting, width=0.4, label='Alighting', color='red', alpha=0.7)
    ax2.plot(hours, net_flow.cumsum(), 'k--', linewidth=2, label='Cumulative Net Flow')
    
    # Alerts on secondary axis
    alerts = hourly_stats[('alert_triggered', '<lambda>')]
    ax2_twin.plot(hours, alerts, 'ro-', linewidth=2, markersize=8, label='Alerts')
    
    ax2.set_xlabel('Hour of Day')
    ax2.set_ylabel('Passenger Flow')
    ax2_twin.set_ylabel('Number of Alerts', color='red')
    ax2_twin.tick_params(axis='y', labelcolor='red')
    ax2.set_title('Hourly Passenger Flow and Alert Patterns', fontsize=14)
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(hours)
    
    plt.tight_layout()
    plt.savefig('KPI/8_peak_hour_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_kpi_summary_dashboard(df):
    """9. KPI Summary Dashboard"""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Calculate KPIs
    max_utilization = df['occupancy_percent'].max()
    avg_utilization = df['occupancy_percent'].mean()
    overcrowded_percentage = (df['status'] == 'OVERCROWDED').sum() / len(df) * 100
    total_alerts = (df['alert_triggered'] == 'Yes').sum()
    total_passengers = df['boarding'].sum()
    avg_sensor_mismatch = df['sensor_mismatch'].mean()
    
    # KPI 1: Utilization Gauge
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.pie([avg_utilization, 100-avg_utilization], 
            colors=['#FF6B6B', '#E0E0E0'], 
            startangle=90, 
            counterclock=False)
    circle = plt.Circle((0,0), 0.7, color='white')
    ax1.add_artist(circle)
    ax1.text(0, 0, f'{avg_utilization:.1f}%', ha='center', va='center', fontsize=24, fontweight='bold')
    ax1.set_title('Average Utilization', fontsize=14, pad=20)
    
    # KPI 2: Total Passengers
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.text(0.5, 0.5, f'{total_passengers:,}', ha='center', va='center', 
             transform=ax2.transAxes, fontsize=36, fontweight='bold', color='#2E86AB')
    ax2.text(0.5, 0.2, 'Total Passengers', ha='center', va='center', 
             transform=ax2.transAxes, fontsize=14)
    ax2.axis('off')
    
    # KPI 3: Alert Count
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.text(0.5, 0.5, f'{total_alerts}', ha='center', va='center', 
             transform=ax3.transAxes, fontsize=36, fontweight='bold', color='#F44336')
    ax3.text(0.5, 0.2, 'Overcrowding Alerts', ha='center', va='center', 
             transform=ax3.transAxes, fontsize=14)
    ax3.axis('off')
    
    # KPI 4: Time distribution
    ax4 = fig.add_subplot(gs[1, :])
    status_colors = {'UNDERCROWDED': '#4CAF50', 'NORMAL': '#2196F3', 
                    'NEARLY_FULL': '#FF9800', 'OVERCROWDED': '#F44336'}
    status_percentages = df['status'].value_counts(normalize=True) * 100
    
    y_pos = 0
    for status in ['UNDERCROWDED', 'NORMAL', 'NEARLY_FULL', 'OVERCROWDED']:
        if status in status_percentages:
            ax4.barh(y_pos, status_percentages[status], color=status_colors[status], 
                    label=f'{status}: {status_percentages[status]:.1f}%')
            y_pos += 1
    
    ax4.set_xlim(0, 100)
    ax4.set_xlabel('Percentage of Time (%)')
    ax4.set_title('Bus Status Distribution Throughout Operation', fontsize=14)
    ax4.legend(loc='right')
    ax4.set_yticks([])
    
    # KPI 5: Hourly pattern
    ax5 = fig.add_subplot(gs[2, :])
    hourly_avg = df.groupby('hour')['occupancy_percent'].mean()
    ax5.bar(hourly_avg.index, hourly_avg.values, 
            color=['red' if x >= 80 else 'orange' if x >= 60 else 'green' for x in hourly_avg.values])
    ax5.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Overcrowded')
    ax5.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='Nearly Full')
    ax5.set_xlabel('Hour of Day')
    ax5.set_ylabel('Average Occupancy %')
    ax5.set_title('Average Hourly Occupancy Levels', fontsize=14)
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)
    
    # Overall title
    fig.suptitle('Smart Bus Overcrowding Detection - KPI Dashboard', fontsize=18, y=0.98)
    
    # Use constrained layout instead of tight_layout
    fig.set_constrained_layout(True)
    plt.savefig('KPI/9_kpi_summary_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all visualizations"""
    print("KPI Visualization Generator")
    print("="*50)
    
    # Read the data
    try:
        df = pd.read_csv('bus_overcrowding_data.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Add hour column if not present
        if 'hour' not in df.columns:
            df['hour'] = df['timestamp'].dt.hour
        
        print(f"Loaded {len(df)} records from bus_overcrowding_data.csv")
        
    except FileNotFoundError:
        print("Error: bus_overcrowding_data.csv not found!")
        print("Please run bus_data_generator.py first to generate the data.")
        return
    
    # Setup plotting style
    setup_plot_style()
    
    # Generate all visualizations
    print("\nGenerating visualizations...")
    
    print("1. Creating line graph - Passenger count over time...")
    create_line_graph_passenger_count(df)
    
    print("2. Creating heatmap - Crowding levels by stop and time...")
    create_heatmap_crowding_levels(df)
    
    print("3. Creating bar chart - Alert frequency by location...")
    create_bar_chart_alerts(df)
    
    print("4. Creating pie chart - Bus status distribution...")
    create_pie_chart_status(df)
    
    print("5. Creating sensor accuracy comparison...")
    create_sensor_comparison_chart(df)
    
    print("6. Creating time series analysis...")
    create_time_series_analysis(df)
    
    print("7. Creating stop performance dashboard...")
    create_stop_performance_dashboard(df)
    
    print("8. Creating peak hour analysis...")
    create_peak_hour_analysis(df)
    
    print("9. Creating KPI summary dashboard...")
    create_kpi_summary_dashboard(df)
    
    print("\n✓ All visualizations generated successfully!")
    print(f"\nFiles saved in 'KPI' folder:")
    print("- 1_passenger_count_over_time.png")
    print("- 2_crowding_heatmap.png")
    print("- 3_alert_frequency_by_location.png")
    print("- 4_status_distribution_pie.png")
    print("- 5_sensor_accuracy_analysis.png")
    print("- 6_time_series_analysis.png")
    print("- 7_stop_performance_dashboard.png")
    print("- 8_peak_hour_analysis.png")
    print("- 9_kpi_summary_dashboard.png")
    
    # Generate a summary report
    generate_visualization_descriptions()

def generate_visualization_descriptions():
    """Generate descriptions for each visualization"""
    descriptions = """
VISUALIZATION DESCRIPTIONS FOR REPORT
=====================================

1. **Passenger Count Over Time (Line Graph)**
   - Shows average passenger count throughout the day with sensor comparison
   - Highlights capacity thresholds and peak usage times
   - Useful for identifying when additional buses are needed

2. **Crowding Levels Heatmap**
   - Displays occupancy patterns across all stops and hours
   - Red boxes indicate critical overcrowding conditions
   - Helps identify problematic stop-time combinations

3. **Alert Frequency Bar Chart**
   - Shows which stops trigger the most overcrowding alerts
   - Includes average line for comparison
   - Guides infrastructure improvement priorities

4. **Bus Status Distribution Pie Chart**
   - Visualizes time spent in each occupancy state
   - Exploded overcrowded segment for emphasis
   - Quantifies overall system performance

5. **Sensor Accuracy Analysis**
   - Compares IR sensor vs camera readings
   - Shows how accuracy varies with occupancy levels
   - Validates sensor fusion approach

6. **Time Series Analysis**
   - Three-panel view of real-time operations
   - Shows passenger count, boarding/alighting, and occupancy
   - Provides detailed operational insights

7. **Stop Performance Dashboard**
   - Four metrics per stop: flow, occupancy, turnover, alerts
   - Comprehensive stop-level analysis
   - Identifies high-demand locations

8. **Peak Hour Analysis**
   - Highlights morning and evening rush hours
   - Shows passenger flow patterns and alert frequency
   - Supports scheduling decisions

9. **KPI Summary Dashboard**
   - Executive-level overview of key metrics
   - Visual KPIs for quick assessment
   - Suitable for management presentations
"""
    
    with open('KPI/visualization_descriptions.txt', 'w', encoding='utf-8') as f:
        f.write(descriptions)
    
    print("\n✓ Visualization descriptions saved to 'KPI/visualization_descriptions.txt'")

if __name__ == "__main__":
    main()