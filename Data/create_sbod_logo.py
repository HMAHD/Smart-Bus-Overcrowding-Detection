import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch
import numpy as np
import os

# Create assets folder if it doesn't exist
if not os.path.exists('assets'):
    os.makedirs('assets')

def create_sbod_logo():
    """Create SBOD logo"""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Background circle
    bg_circle = Circle((5, 5), 4.5, facecolor='#2E86AB', edgecolor='none')
    ax.add_patch(bg_circle)
    
    # Bus icon (simplified)
    bus_body = FancyBboxPatch((2.5, 4), 5, 2.5, 
                              boxstyle="round,pad=0.1",
                              facecolor='white', 
                              edgecolor='#1E5A7B', 
                              linewidth=3)
    ax.add_patch(bus_body)
    
    # Windows
    for i in range(3):
        window = Rectangle((3.2 + i*1.5, 5.2), 0.8, 0.8, 
                          facecolor='#87CEEB', 
                          edgecolor='#1E5A7B',
                          linewidth=2)
        ax.add_patch(window)
    
    # Wheels
    wheel1 = Circle((3.5, 3.8), 0.3, facecolor='#333333')
    wheel2 = Circle((6.5, 3.8), 0.3, facecolor='#333333')
    ax.add_patch(wheel1)
    ax.add_patch(wheel2)
    
    # Signal waves (representing IoT)
    for i in range(3):
        arc = patches.Arc((7.5, 6), 1+i*0.5, 1+i*0.5, 
                         angle=0, theta1=210, theta2=330,
                         color='white', linewidth=2, alpha=0.7-i*0.2)
        ax.add_patch(arc)
    
    # Text
    ax.text(5, 1.5, 'SBOD', fontsize=36, fontweight='bold', 
            ha='center', va='center', color='white', 
            family='Arial Black')
    
    ax.text(5, 0.5, 'Smart Bus Overcrowding Detection', 
            fontsize=10, ha='center', va='center', 
            color='white', style='italic')
    
    plt.tight_layout()
    plt.savefig('assets/sbod_logo.png', dpi=300, bbox_inches='tight', 
                facecolor='none', edgecolor='none', transparent=True)
    plt.close()
    
    # Create a simplified version for favicon
    create_favicon()

def create_favicon():
    """Create simplified favicon version"""
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Background
    bg = Circle((5, 5), 5, facecolor='#2E86AB')
    ax.add_patch(bg)
    
    # Simplified bus
    bus = Rectangle((2, 4), 6, 3, facecolor='white', edgecolor='none')
    ax.add_patch(bus)
    
    # Signal
    for i in range(2):
        arc = patches.Arc((7, 6.5), 2+i, 2+i, 
                         angle=0, theta1=210, theta2=330,
                         color='white', linewidth=3, alpha=0.8-i*0.3)
        ax.add_patch(arc)
    
    plt.tight_layout()
    plt.savefig('assets/sbod_favicon.png', dpi=150, bbox_inches='tight',
                facecolor='none', edgecolor='none', transparent=True)
    plt.close()

def create_banner():
    """Create GitHub banner"""
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis('off')
    
    # Gradient background effect
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, extent=[0, 12, 0, 4], aspect='auto', 
              cmap='Blues_r', alpha=0.8)
    
    # Logo section
    logo_bg = Circle((2, 2), 1.5, facecolor='white', alpha=0.9)
    ax.add_patch(logo_bg)
    
    # Mini bus in logo
    bus = FancyBboxPatch((1, 1.5), 2, 1, 
                        boxstyle="round,pad=0.05",
                        facecolor='#2E86AB', alpha=0.9)
    ax.add_patch(bus)
    
    # Title
    ax.text(5, 2.8, 'Smart Bus Overcrowding Detection', 
            fontsize=28, fontweight='bold', color='#1E5A7B')
    ax.text(5, 2, 'Real-time IoT Solution for Public Transport', 
            fontsize=16, style='italic', color='#2E86AB')
    
    # Features
    features = ['🔢 Dual-Sensor Counting', '📊 Live Monitoring', 
                '🚨 Automated Alerts', '📍 GPS Tracking']
    for i, feature in enumerate(features):
        ax.text(5 + (i-1.5)*2.5, 0.8, feature, fontsize=12, 
                ha='center', color='#333333')
    
    plt.tight_layout()
    plt.savefig('assets/sbod_banner.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()

def main():
    print("Generating SBOD branding assets...")
    
    print("1. Creating main logo...")
    create_sbod_logo()
    
    print("2. Creating favicon...")
    # Already created in create_sbod_logo()
    
    print("3. Creating GitHub banner...")
    create_banner()
    
    print("\nAll assets generated successfully!")
    print("\nFiles saved in 'assets' folder:")
    print("- sbod_logo.png (main logo with transparency)")
    print("- sbod_favicon.png (simplified icon)")
    print("- sbod_banner.png (GitHub repository banner)")

if __name__ == "__main__":
    main()